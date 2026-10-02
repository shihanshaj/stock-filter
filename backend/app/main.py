"""StockLens API — FastAPI application with all endpoints."""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sse_starlette.sse import EventSourceResponse
import uuid
import asyncio
import json
import io
import csv
import logging

from app.database import init_db, get_db, AsyncSessionLocal, ScanRun, ScanResult, Setting
from app.models import ScanDetailResponse, ScansListResponse, SettingsResponse, SettingsUpdate
from app.services.scanner import ScannerService, progress_queues, scan_progress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StockLens API",
    description="Chartink × Moneycontrol Stock Filter",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    await init_db()
    logger.info("StockLens API started")


# =============================================================================
# Health
# =============================================================================

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "stocklens"}


# =============================================================================
# Scans
# =============================================================================

@app.post("/api/scans")
async def start_scan(background_tasks: BackgroundTasks):
    """Start a new scan. Returns scan_id immediately, processing happens in background."""
    scan_id = str(uuid.uuid4())

    async def run_bg_scan(s_id: str):
        async with AsyncSessionLocal() as session:
            scanner = ScannerService(session, concurrency=10)
            await scanner.run_scan(s_id)

    background_tasks.add_task(run_bg_scan, scan_id)
    return {"scan_id": scan_id, "status": "started"}


@app.get("/api/scans/{scan_id}/stream")
async def stream_scan(scan_id: str):
    """SSE stream for real-time scan progress updates."""
    q = asyncio.Queue()
    if scan_id not in progress_queues:
        progress_queues[scan_id] = []
    progress_queues[scan_id].append(q)

    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=60.0)
                    yield {"data": json.dumps(data)}
                    status = data.get("status", "")
                    if status in ("COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED"):
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"data": json.dumps({"keepalive": True})}
        except asyncio.CancelledError:
            pass
        finally:
            if scan_id in progress_queues and q in progress_queues[scan_id]:
                progress_queues[scan_id].remove(q)

    return EventSourceResponse(event_generator())


@app.get("/api/scans")
async def list_scans(db: AsyncSession = Depends(get_db)):
    """List all scan runs, most recent first."""
    result = await db.execute(
        select(ScanRun).order_by(desc(ScanRun.started_at)).limit(50)
    )
    scans = result.scalars().all()
    return {"scans": [_scan_run_to_dict(s) for s in scans]}


@app.get("/api/scans/latest")
async def get_latest_scan(db: AsyncSession = Depends(get_db)):
    """Get the most recent completed scan with results."""
    result = await db.execute(
        select(ScanRun)
        .where(ScanRun.status.in_(["COMPLETED", "COMPLETED_WITH_WARNINGS"]))
        .order_by(desc(ScanRun.started_at))
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="No completed scans found")

    results = await _get_scan_results(db, run.id)
    return {"scan": _scan_run_to_dict(run), "stocks": [_scan_result_to_dict(r) for r in results]}


@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific scan with its results."""
    result = await db.execute(select(ScanRun).where(ScanRun.id == scan_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Scan not found")

    results = await _get_scan_results(db, run.id)
    return {"scan": _scan_run_to_dict(run), "stocks": [_scan_result_to_dict(r) for r in results]}


@app.get("/api/scans/{scan_id}/diff")
async def get_scan_diff(scan_id: str, db: AsyncSession = Depends(get_db)):
    """Compare scan results with the previous scan."""
    scanner = ScannerService(db)
    return await scanner.get_scan_diff(scan_id)


@app.get("/api/scans/{scan_id}/export/csv")
async def export_csv(scan_id: str, db: AsyncSession = Depends(get_db)):
    """Export scan results as CSV."""
    run_result = await db.execute(select(ScanRun).where(ScanRun.id == scan_id))
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Scan not found")

    results = await _get_scan_results(db, scan_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "scan_time", "symbol", "company", "sector", "price",
        "day_change_percent", "mc_score", "growth_trend", "valuation",
        "matched_category", "qualified", "moneycontrol_url"
    ])

    scan_time = run.started_at.isoformat() if run.started_at else ""

    for r in results:
        writer.writerow([
            scan_time,
            r.symbol,
            r.company_name or "",
            r.sector or "",
            r.price or "",
            r.day_change_percent or "",
            r.mc_score or "",
            r.growth_trend or "",
            r.valuation or "",
            r.matched_category or "",
            "Yes" if r.qualified else "No",
            r.moneycontrol_url or "",
        ])

    content = output.getvalue()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=stocklens_scan_{scan_id[:8]}.csv"},
    )


@app.get("/api/scans/{scan_id}/export/json")
async def export_json(scan_id: str, db: AsyncSession = Depends(get_db)):
    """Export scan results as JSON."""
    results = await _get_scan_results(db, scan_id)
    data = [_scan_result_to_dict(r) for r in results]
    return JSONResponse(content=data)


# =============================================================================
# Stocks
# =============================================================================

@app.get("/api/stocks/{symbol}")
async def get_stock(symbol: str, db: AsyncSession = Depends(get_db)):
    """Get latest scan result for a specific stock symbol."""
    result = await db.execute(
        select(ScanResult)
        .where(ScanResult.symbol == symbol.upper())
        .order_by(desc(ScanResult.checked_at))
        .limit(1)
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    return _scan_result_to_dict(stock)


@app.post("/api/stocks/{symbol}/refresh")
async def refresh_stock(symbol: str, background_tasks: BackgroundTasks):
    """Refresh Moneycontrol data for a specific stock."""
    # For now, return acknowledgment — full implementation would re-fetch from MC
    return {"status": "queued", "symbol": symbol.upper()}


# =============================================================================
# Settings
# =============================================================================

@app.get("/api/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Get application settings."""
    result = await db.execute(select(Setting))
    settings = {s.key: s.value for s in result.scalars().all()}

    # Defaults
    defaults = {
        "screener_url": "https://chartink.com/screener/copy-intrinsic-value-stock-134?src=wassup",
        "concurrency": "3",
        "cache_ttl_hours": "1",
        "category_average_discounted": "true",
        "category_average_attractive": "true",
        "category_high_attractive": "true",
        "category_high_high_valuation": "true",
        "theme": "system",
    }

    for key, default in defaults.items():
        if key not in settings:
            settings[key] = default

    return {"settings": settings}


@app.put("/api/settings")
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    """Update application settings."""
    for key, value in data.settings.items():
        existing = await db.execute(select(Setting).where(Setting.key == key))
        obj = existing.scalar_one_or_none()
        if obj:
            obj.value = value
        else:
            db.add(Setting(key=key, value=value))
    await db.commit()
    return await get_settings(db)


# =============================================================================
# Helpers
# =============================================================================

async def _get_scan_results(db: AsyncSession, scan_id: str):
    """Get all results for a scan."""
    result = await db.execute(
        select(ScanResult).where(ScanResult.scan_id == scan_id)
    )
    return result.scalars().all()


def _scan_run_to_dict(run: ScanRun) -> dict:
    """Convert ScanRun ORM object to dict."""
    return {
        "id": run.id,
        "status": run.status.lower() if run.status else "",
        "startTime": run.started_at.isoformat() if run.started_at else None,
        "endTime": run.completed_at.isoformat() if run.completed_at else None,
        "chartinkCount": run.chartink_count or 0,
        "resolvedCount": run.resolved_count or 0,
        "qualifiedCount": run.qualified_count or 0,
        "notQualifiedCount": run.not_qualified_count or 0,
        "needsReviewCount": run.review_count or 0,
        "durationSeconds": run.duration_seconds,
        "screenerUrl": run.screener_url,
    }


def _scan_result_to_dict(r: ScanResult) -> dict:
    """Convert ScanResult ORM object to dict."""
    return {
        "id": r.id,
        "scanId": r.scan_id,
        "symbol": r.symbol,
        "companyName": r.company_name,
        "exchange": r.exchange,
        "sector": r.sector,
        "industry": r.industry,
        "bseCode": r.bse_code,
        "chartinkMatched": r.chartink_matched,
        "moneycontrolResolved": r.moneycontrol_resolved,
        "moneycontrolUrl": r.moneycontrol_url,
        "moneycontrolScId": r.moneycontrol_sc_id,
        "price": r.price,
        "dayChange": r.day_change_percent,
        "mcScore": r.mc_score,
        "qFactor": r.q_factor,
        "gFactor": r.g_factor,
        "vFactor": r.v_factor,
        "classification": r.raw_classification,
        "financialStrength": r.financial_strength,
        "growthTrend": r.growth_trend,
        "valuation": r.valuation,
        "category": r.matched_category,
        "verified": r.qualified,
        "status": r.status,
        "needsReview": r.status == "ERROR" or r.error_message is not None,
        "error": r.error_message,
        "lastChecked": r.checked_at.isoformat() if r.checked_at else None,
    }
