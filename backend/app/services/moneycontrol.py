"""Moneycontrol service: search, resolve, and extract stock classifications."""

import httpx
import re
import asyncio
import logging
import random
from typing import Optional, List, Dict, Any

from bs4 import BeautifulSoup
from html import unescape

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.moneycontrol.com/',
}


class MoneycontrolService:
    """Handles all Moneycontrol API interactions."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=HEADERS,
        )
        self.search_url = "https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php"
        self.signal_url = "https://www.moneycontrol.com/mc/widget/mcsignalwidget/get_powerful_signal"
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def search_stock(self, query: str) -> List[Dict[str, Any]]:
        """Search Moneycontrol for a stock by symbol or name.
        
        Returns list of matching entries with sc_id, link_src, stock_name, pdt_dis_nm, etc.
        """
        params = {
            'classic': 'true',
            'query': query,
            'type': '1',
            'format': 'json',
        }
        headers = {
            **HEADERS,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
        }

        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(
                    self.search_url, params=params, headers=headers
                )
                response.raise_for_status()
                text = response.text.strip()
                if not text or text.startswith('<'):
                    return []
                return response.json()
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(f"MC search attempt {attempt + 1} failed for '{query}': {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"MC search failed for '{query}' after {self.max_retries} attempts: {e}")
                    return []

    async def get_stock_classification(self, sc_id: str, link_src: str = "") -> Optional[Dict[str, Any]]:
        """Get stock classification from Moneycontrol.
        
        Primary: Use the powerful_signal widget API.
        Fallback: Scrape the stock score page.
        
        Returns dict with: raw_classification, mc_score, url, q_factor, g_factor, v_factor
        """
        # Try the widget API first
        result = await self._fetch_via_signal_widget(sc_id, link_src)
        if result and result.get('raw_classification'):
            return result

        # Fallback: try the stock score page
        if link_src:
            slug = self._extract_slug_from_link(link_src)
            if slug:
                result = await self._fetch_via_score_page(slug, sc_id)
                if result and result.get('raw_classification'):
                    return result

        # Fallback: try the main stock page
        if link_src:
            result = await self._fetch_via_stock_page(link_src)
            if result and result.get('raw_classification'):
                return result

        return result

    async def _fetch_via_signal_widget(self, sc_id: str, referer: str = "") -> Optional[Dict[str, Any]]:
        """Fetch classification via the MC Insights powerful signal widget API."""
        params = {
            'classic': 'true',
            'scId': sc_id,
        }
        headers = {
            **HEADERS,
            'Accept': 'text/html, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
        }
        if referer:
            headers['Referer'] = referer

        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(
                    self.signal_url, params=params, headers=headers
                )
                if response.status_code == 400:
                    # "Bad request" - endpoint might not support this sc_id format
                    logger.debug(f"Signal widget returned 400 for sc_id={sc_id}")
                    return None
                response.raise_for_status()

                html_text = response.text
                return self._parse_signal_html(html_text, sc_id)

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (403, 429):
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0.5, 2.0)
                    logger.warning(f"Rate limited on signal widget for {sc_id}. Waiting {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Signal widget error for {sc_id}: {e}")
                    return None
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Signal widget failed for {sc_id}: {e}")
                    return None
        return None

    def _parse_signal_html(self, html_text: str, sc_id: str) -> Optional[Dict[str, Any]]:
        """Parse the powerful signal widget HTML response to extract classification."""
        if not html_text or 'Bad request' in html_text:
            return None

        soup = BeautifulSoup(html_text, 'html.parser')
        full_text = soup.get_text(separator=' ', strip=True)

        # Extract the classification sentence
        classification = self._extract_classification_from_text(full_text)

        # Extract MC Score (pattern: "XX/100" or "XX / 100")
        mc_score = None
        score_match = re.search(r'(\d{1,3})\s*/\s*100', full_text)
        if score_match:
            mc_score = int(score_match.group(1))

        return {
            'raw_classification': classification,
            'mc_score': mc_score,
            'url': f"https://www.moneycontrol.com/markets/stocks-score/?scId={sc_id}",
            'q_factor': None,
            'g_factor': None,
            'v_factor': None,
        }

    async def _fetch_via_score_page(self, slug: str, sc_id: str) -> Optional[Dict[str, Any]]:
        """Fetch classification from the MC stocks-score page."""
        url = f"https://www.moneycontrol.com/markets/stocks-score/{slug}-{sc_id}/"

        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url, headers=HEADERS)
                if response.status_code == 404:
                    return None
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                full_text = soup.get_text(separator=' ', strip=True)

                classification = self._extract_classification_from_text(full_text)

                mc_score = None
                score_match = re.search(r'(\d{1,3})\s*/\s*100', full_text)
                if score_match:
                    mc_score = int(score_match.group(1))

                return {
                    'raw_classification': classification,
                    'mc_score': mc_score,
                    'url': url,
                    'q_factor': None,
                    'g_factor': None,
                    'v_factor': None,
                }
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (403, 429):
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0.5, 2.0)
                    await asyncio.sleep(delay)
                else:
                    return None
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Score page failed for {sc_id}: {e}")
                    return None
        return None

    async def _fetch_via_stock_page(self, link_src: str) -> Optional[Dict[str, Any]]:
        """Fallback: try to extract classification from the main stock page."""
        for attempt in range(2):
            try:
                response = await self.client.get(link_src, headers=HEADERS)
                response.raise_for_status()

                full_text = response.text
                classification = self._extract_classification_from_text(full_text)

                mc_score = None
                score_match = re.search(r'(\d{1,3})\s*/\s*100', full_text)
                if score_match:
                    mc_score = int(score_match.group(1))

                return {
                    'raw_classification': classification,
                    'mc_score': mc_score,
                    'url': link_src,
                    'q_factor': None,
                    'g_factor': None,
                    'v_factor': None,
                }
            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(1)
                else:
                    logger.error(f"Stock page failed for {link_src}: {e}")
                    return None
        return None

    def _extract_classification_from_text(self, text: str) -> Optional[str]:
        """Extract the classification sentence from text content.
        
        Pattern: "[Quality] Financial Strength, [Growth] Growth Trend Stock [at/Priced at] [Valuation] Valuations"
        """
        if not text:
            return None

        # Normalize text
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text)

        # Classification pattern - matches the full sentence
        pattern = (
            r'((?:Superior|Average|Good|Strong|Moderate|Weak|Low|High|Poor)\s+'
            r'Financial\s+Strength)'
            r',?\s*'
            r'((?:High|Average|Low|Moderate|Strong|Excellent)\s+'
            r'Growth\s+Trend\s+Stock)'
            r'\s+'
            r'(?:at|Priced\s+at)\s+'
            r'((?:Attractive|Discounted|Reasonable|Fair|High|Expensive|Premium|Low|Moderate)\s+'
            r'Valuations?)'
        )

        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()

        return None

    def _extract_slug_from_link(self, link_src: str) -> str:
        """Extract slug from link_src URL."""
        if not link_src:
            return ''
        parts = [p for p in link_src.rstrip('/').split('/') if p]
        if len(parts) >= 2:
            return parts[-2]
        return ''

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
