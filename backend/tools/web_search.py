"""
BrahmaAI Web Search Tool
Searches the web via SerpAPI (primary) or DuckDuckGo (fallback).
"""

import logging
from typing import Any

from backend.tools.registry import BaseTool
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """
    Web Search Tool: Retrieves current information from the web.
    Uses SerpAPI if key is configured, otherwise falls back to DuckDuckGo.
    """

    name = "web_search"
    description = "Search the web for current information on any topic"
    args = {
        "query": "str: The search query",
        "num_results": "int: Number of results to return (default: 5)",
    }

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a web search.

        Returns:
            {status, query, results: [{title, url, snippet}]}
        """
        logger.info(f"[WebSearchTool] Searching: {query}")

        if settings.SERPAPI_KEY:
            return await self._serpapi_search(query, num_results)
        else:
            return await self._duckduckgo_search(query, num_results)

    async def _serpapi_search(
        self, query: str, num_results: int
    ) -> dict[str, Any]:
        """Search via SerpAPI."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "q": query,
                        "api_key": settings.SERPAPI_KEY,
                        "num": num_results,
                        "engine": "google",
                    },
                )
                data = response.json()
                results = []
                for item in data.get("organic_results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                    })
                return {
                    "status": "success",
                    "query": query,
                    "results": results,
                    "output": self._format_results(query, results),
                }
        except Exception as e:
            logger.error(f"[WebSearchTool] SerpAPI error: {e}")
            return await self._duckduckgo_search(query, num_results)

    async def _duckduckgo_search(
        self, query: str, num_results: int
    ) -> dict[str, Any]:
        """Search via DuckDuckGo (no API key required)."""
        try:
            from duckduckgo_search import AsyncDDGS
            async with AsyncDDGS() as ddgs:
                raw_results = await ddgs.atext(
                    query, max_results=num_results
                )
                results = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in raw_results
                ]
                return {
                    "status": "success",
                    "query": query,
                    "results": results,
                    "output": self._format_results(query, results),
                }
        except ImportError:
            return self._mock_search(query, num_results)
        except Exception as e:
            logger.error(f"[WebSearchTool] DuckDuckGo error: {e}")
            return self._mock_search(query, num_results)

    def _mock_search(self, query: str, num_results: int) -> dict[str, Any]:
        """Mock search results for demo mode."""
        results = [
            {
                "title": f"Result {i+1}: {query}",
                "url": f"https://example.com/result-{i+1}",
                "snippet": f"This is a mock search result about '{query}'. "
                           f"Install duckduckgo-search or set SERPAPI_KEY for real results.",
            }
            for i in range(min(num_results, 3))
        ]
        return {
            "status": "success",
            "query": query,
            "results": results,
            "output": self._format_results(query, results),
            "note": "Mock results — install duckduckgo-search for real web search",
        }

    def _format_results(
        self, query: str, results: list[dict[str, Any]]
    ) -> str:
        lines = [f"Search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(
                f"{i}. **{r['title']}**\n"
                f"   URL: {r['url']}\n"
                f"   {r['snippet']}\n"
            )
        return "\n".join(lines)
