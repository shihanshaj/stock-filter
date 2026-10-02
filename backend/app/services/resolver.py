"""Symbol resolver: maps Chartink NSE symbols to Moneycontrol company identifiers."""

import re
import logging
from html import unescape
from typing import Optional, Dict
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from app.services.moneycontrol import MoneycontrolService

logger = logging.getLogger(__name__)


class ResolverService:
    """Resolves NSE ticker symbols from Chartink to Moneycontrol sc_id and metadata."""

    def __init__(self, mc_service: MoneycontrolService, db=None):
        self.mc = mc_service
        self.db = db
        self._cache: Dict[str, dict] = {}

    async def resolve_symbol(self, symbol: str) -> Optional[dict]:
        """Resolve an NSE symbol to Moneycontrol company info.

        Returns dict with keys: sc_id, company_name, slug, sector, link_src, bse_code, isin
        or None if not found.
        """
        symbol = symbol.strip().upper()

        # Check in-memory cache first
        if symbol in self._cache:
            return self._cache[symbol]

        # Check database cache
        if self.db:
            from sqlalchemy import select
            from app.database import MoneycontrolCache
            result = await self.db.execute(
                select(MoneycontrolCache).where(MoneycontrolCache.symbol == symbol)
            )
            cached = result.scalar_one_or_none()
            if cached:
                data = {
                    'sc_id': cached.sc_id,
                    'company_name': cached.company_name,
                    'slug': cached.slug,
                    'sector': cached.sector,
                    'link_src': cached.link_src,
                    'bse_code': cached.bse_code,
                    'isin': cached.isin,
                }
                self._cache[symbol] = data
                return data

        # Search Moneycontrol
        results = await self.mc.search_stock(symbol)
        if not results:
            logger.warning(f"No Moneycontrol results for symbol: {symbol}")
            return None

        for entry in results:
            pdt_dis_nm = entry.get('pdt_dis_nm', '')
            # pdt_dis_nm format: "Company Name&nbsp;<span>ISIN, NSE_SYMBOL, BSE_CODE</span>"
            # Parse the span content to extract ISIN, NSE symbol, BSE code
            parsed = self._parse_pdt_dis_nm(pdt_dis_nm)

            if parsed and parsed.get('nse_symbol', '').upper() == symbol.upper():
                # Exact NSE symbol match confirmed
                link_src = entry.get('link_src', '')
                slug = self._extract_slug(link_src)
                sc_id = entry.get('sc_id', '')

                resolved = {
                    'sc_id': sc_id,
                    'company_name': entry.get('stock_name') or entry.get('name', ''),
                    'slug': slug,
                    'sector': entry.get('sc_sector', ''),
                    'link_src': link_src,
                    'bse_code': parsed.get('bse_code'),
                    'isin': parsed.get('isin'),
                }

                # Cache the result
                self._cache[symbol] = resolved
                if self.db:
                    await self._save_to_cache(symbol, resolved)

                return resolved

        # If no exact NSE match, try a broader search with company name patterns
        # but only accept if we can verify the ticker
        logger.warning(f"No exact NSE match found for {symbol} in {len(results)} results")
        return None

    def _parse_pdt_dis_nm(self, pdt_dis_nm: str) -> Optional[dict]:
        """Parse the pdt_dis_nm field to extract ISIN, NSE symbol, and BSE code.

        Format: "Company Name&nbsp;<span>INE..., NSESYMBOL, 123456</span>"
        """
        if not pdt_dis_nm:
            return None

        # Decode HTML entities
        text = unescape(pdt_dis_nm)

        # Extract content within <span> tags
        soup = BeautifulSoup(text, 'html.parser')
        span = soup.find('span')
        if not span:
            return None

        span_text = span.get_text(strip=True)
        parts = [p.strip() for p in span_text.split(',')]

        result = {}
        for part in parts:
            part = part.strip()
            if re.match(r'^INE[A-Z0-9]+$', part):
                result['isin'] = part
            elif re.match(r'^[A-Z][A-Z0-9_-]+$', part) and not part.isdigit():
                result['nse_symbol'] = part
            elif re.match(r'^\d+$', part):
                result['bse_code'] = part

        return result if result.get('nse_symbol') else None

    def _extract_slug(self, link_src: str) -> str:
        """Extract the company slug from a Moneycontrol URL.

        URL format: https://www.moneycontrol.com/india/stockpricequote/sector/companyslug/SC_ID
        """
        if not link_src:
            return ''

        parts = [p for p in link_src.rstrip('/').split('/') if p]
        # slug is second-to-last, sc_id is last
        if len(parts) >= 2:
            return parts[-2]
        return ''

    async def _save_to_cache(self, symbol: str, data: dict):
        """Save resolved mapping to database cache."""
        try:
            from app.database import MoneycontrolCache
            now = datetime.now(timezone.utc)
            cache_entry = MoneycontrolCache(
                symbol=symbol,
                sc_id=data['sc_id'],
                company_name=data['company_name'],
                slug=data['slug'],
                sector=data.get('sector'),
                link_src=data.get('link_src'),
                isin=data.get('isin'),
                bse_code=data.get('bse_code'),
                created_at=now,
                updated_at=now,
            )
            
            # Use lock if available to prevent concurrent SQLite write issues
            if hasattr(self, 'db_lock') and self.db_lock:
                async with self.db_lock:
                    await self._do_cache_write(symbol, data, cache_entry, now)
            else:
                await self._do_cache_write(symbol, data, cache_entry, now)
                
        except Exception as e:
            logger.error(f"Failed to cache mapping for {symbol}: {e}")

    async def _do_cache_write(self, symbol, data, cache_entry, now):
        from sqlalchemy import select
        from app.database import MoneycontrolCache as MC
        existing = await self.db.execute(select(MC).where(MC.symbol == symbol))
        if existing.scalar_one_or_none():
            # Update existing
            await self.db.execute(
                MC.__table__.update().where(MC.symbol == symbol).values(
                    sc_id=data['sc_id'],
                    company_name=data['company_name'],
                    slug=data['slug'],
                    sector=data.get('sector'),
                    link_src=data.get('link_src'),
                    isin=data.get('isin'),
                    bse_code=data.get('bse_code'),
                    updated_at=now,
                )
            )
        else:
            self.db.add(cache_entry)
        await self.db.flush()
