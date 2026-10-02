"""Chartink screener extraction service."""

import httpx
import re
import asyncio
import logging
import random
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_SCAN_CLAUSE = "( {cash} ( daily vwap <= ( ( ttm eps * 1.135 * ( 20 + ttm pe ) ) * 0.666 ) and ttm pe > 9 ) )"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


class ChartinkService:
    """Fetches stock screener results from Chartink."""

    def __init__(self, screener_url: str = None, max_retries: int = 3):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=HEADERS)
        self.base_url = "https://chartink.com"
        self.screener_url = screener_url or "https://chartink.com/screener/copy-intrinsic-value-stock-134?src=wassup"
        self.process_url = f"{self.base_url}/screener/process"
        self.max_retries = max_retries

    async def get_stocks(self, scan_clause: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch screener results from Chartink.
        
        1. GET the screener page to obtain CSRF token
        2. Optionally extract scan_clause from the page's atlas_query
        3. POST to /screener/process with the scan clause
        
        Returns list of stock dicts with keys: sr, name, nsecode, bsecode, per_chg, close, volume
        """
        csrf_token = await self._get_csrf_token()
        if not csrf_token:
            raise ValueError("Could not obtain CSRF token from Chartink")

        if not scan_clause:
            scan_clause = DEFAULT_SCAN_CLAUSE

        return await self._run_scan(csrf_token, scan_clause)

    async def _get_csrf_token(self) -> Optional[str]:
        """Get CSRF token from the Chartink screener page."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(self.screener_url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                meta = soup.find('meta', {'name': 'csrf-token'})
                if meta and meta.get('content'):
                    return meta['content']

                logger.error("CSRF token meta tag not found in Chartink page")
                return None

            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Chartink CSRF attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed to get Chartink CSRF token after {self.max_retries} attempts: {e}")
                    raise

    async def _run_scan(self, csrf_token: str, scan_clause: str) -> List[Dict[str, Any]]:
        """POST to Chartink's process endpoint to get screener results."""
        headers = {
            'X-CSRF-TOKEN': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': self.screener_url,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        payload = {'scan_clause': scan_clause}

        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    self.process_url, headers=headers, data=payload
                )
                response.raise_for_status()
                data = response.json()

                stocks = data.get('data', [])
                logger.info(f"Chartink returned {len(stocks)} stocks")

                # Normalize: ensure each stock has expected fields
                normalized = []
                seen_symbols = set()
                for stock in stocks:
                    symbol = (stock.get('nsecode') or '').strip().upper()
                    if not symbol or symbol in seen_symbols:
                        continue
                    seen_symbols.add(symbol)

                    normalized.append({
                        'sr': stock.get('sr'),
                        'name': (stock.get('name') or '').strip(),
                        'nsecode': symbol,
                        'bsecode': (stock.get('bsecode') or '').strip(),
                        'per_chg': stock.get('per_chg'),
                        'close': stock.get('close'),
                        'volume': stock.get('volume'),
                    })

                return normalized

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 419:
                    # CSRF expired — get a new token
                    logger.warning("Chartink CSRF expired (419). Refreshing token...")
                    csrf_token = await self._get_csrf_token()
                    if csrf_token:
                        headers['X-CSRF-TOKEN'] = csrf_token
                    continue
                if attempt < self.max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Chartink scan attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    raise

        return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
