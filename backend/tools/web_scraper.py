"""
BrahmaAI Web Scraper Tool
Fetches and cleans content from web pages.
"""

import logging
import re
from typing import Any

from backend.tools.registry import BaseTool

logger = logging.getLogger(__name__)


class WebScraperTool(BaseTool):
    name = "web_scraper"
    description = "Fetch and extract clean text content from a web URL"
    args = {
        "url": "str: The URL to scrape",
        "max_chars": "int: Maximum characters to return (default: 3000)",
    }

    async def execute(
        self,
        url: str,
        max_chars: int = 3000,
        **kwargs: Any,
    ) -> dict[str, Any]:
        logger.info(f"[WebScraperTool] Scraping: {url}")
        try:
            import httpx
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                headers={"User-Agent": "BrahmaAI/1.0 (+https://brahmaai.dev)"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")

                if "text/html" in content_type:
                    text = self._extract_text_from_html(response.text)
                else:
                    text = response.text

                text = text[:max_chars]
                return {
                    "status": "success",
                    "url": url,
                    "output": text,
                    "char_count": len(text),
                }
        except Exception as e:
            logger.error(f"[WebScraperTool] Error scraping {url}: {e}")
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "output": f"Failed to scrape {url}: {e}",
            }

    def _extract_text_from_html(self, html: str) -> str:
        """Extract readable text from HTML using basic parsing."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts, styles, nav, footer
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            # Collapse whitespace
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text.strip()
        except ImportError:
            # Fallback: strip HTML tags with regex
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text)
            return text.strip()
