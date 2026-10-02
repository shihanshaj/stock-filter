"""Scan orchestration: coordinates the full scan workflow with progress reporting."""

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import ScanRun, ScanResult, MoneycontrolCache, ClassificationCache
from app.services.chartink import ChartinkService
from app.services.moneycontrol import MoneycontrolService
from app.services.resolver import ResolverService
from app.services.classifier import ClassifierService

logger = logging.getLogger(__name__)

# Global progress tracking
scan_progress: Dict[str, Dict[str, Any]] = {}
progress_queues: Dict[str, list] = {}


async def broadcast_progress(scan_id: str, data: dict):
    """Send progress update to all connected SSE clients for a scan."""
    if scan_id in progress_queues:
        for q in progress_queues[scan_id]:
            try:
                await q.put(data)
            except Exception:
                pass


class ScannerService:
    """Orchestrates the complete scan workflow."""

    def __init__(self, db: AsyncSession, concurrency: int = 3):
        self.db = db
        self.chartink = ChartinkService()
        self.mc = MoneycontrolService()
        self.resolver = ResolverService(self.mc, db=db)
        self.semaphore = asyncio.Semaphore(concurrency)
        self.concurrency = concurrency
        self.classifier = ClassifierService()
        self.db_lock = asyncio.Lock()
        
        # Give resolver access to the lock
        self.resolver.db_lock = self.db_lock

    async def run_scan(self, scan_id: str, scan_clause: str = None):
        """Execute a full scan: Chartink → Resolve → Classify → Store."""
        start_time = datetime.now(timezone.utc)

        # Create scan run record
        run = ScanRun(
            id=scan_id,
            status="RUNNING",
            started_at=start_time,
            chartink_count=0,
            resolved_count=0,
            qualified_count=0,
            not_qualified_count=0,
            review_count=0,
        )
        self.db.add(run)
        await self.db.commit()

        # Track progress
        progress = {
            "scan_id": scan_id,
            "status": "FETCHING_CHARTINK",
            "stage": "Fetching Chartink screener",
            "processed": 0,
            "total": 0,
            "recent": [],
        }
        scan_progress[scan_id] = progress
        await broadcast_progress(scan_id, progress)

        try:
            # Phase 1: Fetch Chartink stocks
            stocks = await self.chartink.get_stocks(scan_clause)
            run.chartink_count = len(stocks)
            await self.db.commit()

            if not stocks:
                run.status = "COMPLETED"
                run.completed_at = datetime.now(timezone.utc)
                run.duration_seconds = (run.completed_at - start_time).total_seconds()
                await self.db.commit()

                progress["status"] = "COMPLETED"
                progress["stage"] = "No stocks found"
                await broadcast_progress(scan_id, progress)
                return

            progress["status"] = "RESOLVING_STOCKS"
            progress["stage"] = "Resolving stocks on Moneycontrol"
            progress["total"] = len(stocks)
            await broadcast_progress(scan_id, progress)

            # Phase 2: Process each stock
            qualified_count = 0
            not_qualified_count = 0
            review_count = 0
            resolved_count = 0

            async def process_one(stock: dict, index: int):
                nonlocal qualified_count, not_qualified_count, review_count, resolved_count

                async with self.semaphore:
                    symbol = stock['nsecode']
                    company_name = stock.get('name', '')

                    # Add small jitter between requests
                    await asyncio.sleep(random.uniform(0.1, 0.3))

                    # Update progress
                    progress["recent"] = progress.get("recent", [])[-9:] + [
                        {"symbol": symbol, "status": "checking"}
                    ]
                    await broadcast_progress(scan_id, progress)

                    result = ScanResult(
                        scan_id=scan_id,
                        symbol=symbol,
                        company_name=company_name,
                        exchange="NSE",
                        bse_code=stock.get('bsecode'),
                        price=stock.get('close'),
                        day_change_percent=stock.get('per_chg'),
                        chartink_matched=True,
                        moneycontrol_resolved=False,
                        qualified=False,
                        status="PROCESSING",
                        checked_at=datetime.now(timezone.utc),
                    )

                    try:
                        # Step 1: Resolve symbol
                        resolved = await self.resolver.resolve_symbol(symbol)

                        if resolved:
                            result.moneycontrol_resolved = True
                            result.moneycontrol_sc_id = resolved['sc_id']
                            result.moneycontrol_url = resolved.get('link_src', '')
                            result.sector = resolved.get('sector', '')
                            if resolved.get('company_name'):
                                result.company_name = resolved['company_name']
                            if resolved.get('bse_code'):
                                result.bse_code = resolved['bse_code']
                            resolved_count += 1

                            # Step 2: Get classification
                            mc_data = await self.mc.get_stock_classification(
                                resolved['sc_id'],
                                resolved.get('link_src', '')
                            )

                            if mc_data:
                                result.raw_classification = mc_data.get('raw_classification')
                                result.mc_score = mc_data.get('mc_score')
                                result.moneycontrol_url = mc_data.get('url', result.moneycontrol_url)
                                result.q_factor = mc_data.get('q_factor')
                                result.g_factor = mc_data.get('g_factor')
                                result.v_factor = mc_data.get('v_factor')

                                # Step 3: Classify
                                if result.raw_classification:
                                    fs, gt, val, category = self.classifier.classify(
                                        result.raw_classification
                                    )
                                    result.financial_strength = fs
                                    result.growth_trend = gt
                                    result.valuation = val
                                    result.matched_category = category

                                    if category:
                                        result.qualified = True
                                        qualified_count += 1
                                        stock_status = "match"
                                    else:
                                        not_qualified_count += 1
                                        stock_status = "not_selected"
                                else:
                                    result.error_message = "Classification text not found on Moneycontrol"
                                    review_count += 1
                                    stock_status = "review"
                            else:
                                result.error_message = "Could not fetch Moneycontrol classification"
                                review_count += 1
                                stock_status = "review"
                        else:
                            result.error_message = "Could not resolve on Moneycontrol"
                            review_count += 1
                            stock_status = "review"

                        result.status = "SUCCESS"

                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}", exc_info=True)
                        result.status = "ERROR"
                        result.error_message = str(e)[:500]
                        review_count += 1
                        stock_status = "error"

                    async with self.db_lock:
                        self.db.add(result)
                        await self.db.flush()

                    # Update progress
                    progress["processed"] = progress.get("processed", 0) + 1
                    # Update recent activity
                    recent = progress.get("recent", [])
                    for item in recent:
                        if item["symbol"] == symbol:
                            item["status"] = stock_status
                            break
                    await broadcast_progress(scan_id, progress)

            # Process stocks concurrently with controlled concurrency
            tasks = [process_one(stock, i) for i, stock in enumerate(stocks)]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Finalize
            run.resolved_count = resolved_count
            run.qualified_count = qualified_count
            run.not_qualified_count = not_qualified_count
            run.review_count = review_count

            if review_count > 0 and qualified_count + not_qualified_count > 0:
                run.status = "COMPLETED_WITH_WARNINGS"
            else:
                run.status = "COMPLETED"

            run.completed_at = datetime.now(timezone.utc)
            run.duration_seconds = (run.completed_at - start_time).total_seconds()

            await self.db.commit()

            progress["status"] = run.status
            progress["stage"] = "Scan complete"
            progress["qualified_count"] = qualified_count
            progress["not_qualified_count"] = not_qualified_count
            progress["review_count"] = review_count
            progress["resolved_count"] = resolved_count
            progress["duration"] = run.duration_seconds
            await broadcast_progress(scan_id, progress)

        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {e}", exc_info=True)
            run.status = "FAILED"
            run.completed_at = datetime.now(timezone.utc)
            run.duration_seconds = (run.completed_at - start_time).total_seconds()
            await self.db.commit()

            progress["status"] = "FAILED"
            progress["error"] = str(e)
            await broadcast_progress(scan_id, progress)

        finally:
            await self.chartink.close()
            await self.mc.close()

    async def get_scan_diff(self, scan_id: str) -> Dict[str, Any]:
        """Compare a scan with the previous scan to find changes."""
        # Get current scan results
        current_results = await self.db.execute(
            select(ScanResult).where(ScanResult.scan_id == scan_id)
        )
        current = {r.symbol: r for r in current_results.scalars().all()}

        # Get previous scan
        current_run = await self.db.execute(
            select(ScanRun).where(ScanRun.id == scan_id)
        )
        run = current_run.scalar_one_or_none()
        if not run:
            return {"added": [], "removed": [], "changed": [], "unchanged": []}

        prev_run = await self.db.execute(
            select(ScanRun)
            .where(ScanRun.id != scan_id)
            .where(ScanRun.started_at < run.started_at)
            .where(ScanRun.status.in_(["COMPLETED", "COMPLETED_WITH_WARNINGS"]))
            .order_by(desc(ScanRun.started_at))
            .limit(1)
        )
        prev = prev_run.scalar_one_or_none()
        if not prev:
            # No previous scan — all current qualified are "new"
            added = [
                {"symbol": r.symbol, "company": r.company_name, "category": r.matched_category}
                for r in current.values() if r.qualified
            ]
            return {"added": added, "removed": [], "changed": [], "unchanged": []}

        # Get previous scan results
        prev_results = await self.db.execute(
            select(ScanResult).where(ScanResult.scan_id == prev.id)
        )
        previous = {r.symbol: r for r in prev_results.scalars().all()}

        # Compare qualified stocks
        current_qualified = {s: r for s, r in current.items() if r.qualified}
        prev_qualified = {s: r for s, r in previous.items() if r.qualified}

        added = []
        removed = []
        changed = []
        unchanged = []

        for symbol, result in current_qualified.items():
            if symbol not in prev_qualified:
                added.append({
                    "symbol": symbol,
                    "company": result.company_name,
                    "category": result.matched_category,
                })
            elif result.matched_category != prev_qualified[symbol].matched_category:
                changed.append({
                    "symbol": symbol,
                    "company": result.company_name,
                    "from_category": prev_qualified[symbol].matched_category,
                    "to_category": result.matched_category,
                })
            else:
                unchanged.append({
                    "symbol": symbol,
                    "company": result.company_name,
                    "category": result.matched_category,
                })

        for symbol, result in prev_qualified.items():
            if symbol not in current_qualified:
                removed.append({
                    "symbol": symbol,
                    "company": result.company_name,
                    "category": result.matched_category,
                })

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "unchanged": unchanged,
            "previous_scan_id": prev.id,
            "previous_scan_date": prev.started_at.isoformat() if prev.started_at else None,
        }
