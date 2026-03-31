"""
BrahmaAI Researcher Agent
Specialised agent for multi-source research tasks.
Autonomously searches, scrapes, synthesises and cites sources.
"""

import logging
from typing import Any

from backend.core.llm_client import get_llm_client
from backend.tools.registry import get_tool_registry

logger = logging.getLogger(__name__)

RESEARCHER_SYSTEM_PROMPT = """You are the BrahmaAI Research Agent — a specialist in deep, 
multi-source research synthesis.

Given a research query and collected sources, your job is to:
1. Extract the most relevant facts, data points, and insights from each source
2. Cross-reference and validate claims across sources
3. Identify consensus views vs. contested claims
4. Structure findings into a clear, cited report

Output Format:
- Executive Summary (2-3 sentences)
- Key Findings (bullet points with source attribution)
- Analysis (structured prose)
- Sources (numbered list)
- Confidence Level: HIGH / MEDIUM / LOW (based on source quality)

Be accurate. Only state what the sources support. Flag uncertainty explicitly.
"""

QUERY_EXPANSION_PROMPT = """You are a search query specialist.
Given a research goal, generate 3-5 diverse search queries that together will 
provide comprehensive coverage of the topic.

Rules:
- Queries should be complementary, not redundant
- Include: general overview, recent developments, specific aspects, counterpoints
- Keep each query under 10 words
- Return ONLY a JSON array of query strings: ["query 1", "query 2", ...]
"""


class ResearcherAgent:
    """
    Researcher Agent: Conducts deep multi-source research autonomously.
    
    Unlike the base Executor which runs one tool per step, the Researcher
    fans out across multiple searches, scrapes top results, and synthesises
    findings into a structured report with citations.
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.registry = get_tool_registry()

    async def research(
        self,
        query: str,
        depth: int = 3,
        scrape_top_n: int = 2,
    ) -> dict[str, Any]:
        """
        Conduct comprehensive research on a query.

        Args:
            query: Research question or topic
            depth: Number of search queries to expand to (2-5)
            scrape_top_n: How many URLs to deep-scrape per query

        Returns:
            Structured research report with sources and confidence level
        """
        logger.info(f"[ResearcherAgent] Researching: {query[:80]}")

        # --- Step 1: Expand query into multiple searches ---
        queries = await self._expand_query(query, depth)
        logger.info(f"[ResearcherAgent] Expanded to {len(queries)} queries")

        # --- Step 2: Execute all searches ---
        all_results: list[dict[str, Any]] = []
        if self.registry.has_tool("web_search"):
            search_tool = self.registry.get_tool("web_search")
            for q in queries:
                try:
                    result = await search_tool.execute(query=q, num_results=3)
                    if result.get("status") == "success":
                        for r in result.get("results", []):
                            r["search_query"] = q
                            all_results.append(r)
                except Exception as e:
                    logger.warning(f"[ResearcherAgent] Search failed for '{q}': {e}")

        # --- Step 3: Deep-scrape top URLs ---
        scraped_content: list[dict[str, Any]] = []
        if self.registry.has_tool("web_scraper") and all_results:
            scraper = self.registry.get_tool("web_scraper")
            # Pick top N unique URLs across all queries
            seen_urls: set[str] = set()
            urls_to_scrape = []
            for r in all_results:
                url = r.get("url", "")
                if url and url not in seen_urls and len(urls_to_scrape) < scrape_top_n * len(queries):
                    seen_urls.add(url)
                    urls_to_scrape.append(r)

            for item in urls_to_scrape[:scrape_top_n * depth]:
                try:
                    scraped = await scraper.execute(url=item["url"], max_chars=2000)
                    if scraped.get("status") == "success":
                        scraped_content.append({
                            "url":   item["url"],
                            "title": item.get("title", ""),
                            "query": item.get("search_query", ""),
                            "content": scraped["output"],
                        })
                except Exception as e:
                    logger.warning(f"[ResearcherAgent] Scrape failed: {e}")

        # --- Step 4: Synthesise into a report ---
        report = await self._synthesise(query, all_results, scraped_content)

        return {
            "status":      "success",
            "query":        query,
            "queries_used": queries,
            "sources_found": len(all_results),
            "sources_scraped": len(scraped_content),
            "report":       report,
            "output":       report.get("full_text", ""),
        }

    async def _expand_query(self, query: str, depth: int) -> list[str]:
        """Expand a single query into multiple targeted search queries."""
        try:
            response = await self.llm.complete(
                system=QUERY_EXPANSION_PROMPT,
                user=f"Research goal: {query}\nGenerate {depth} search queries.",
                json_mode=True,
                temperature=0.3,
            )
            queries = self.llm.parse_json(response)
            if isinstance(queries, list):
                return queries[:depth]
            # Handle {"queries": [...]} shape
            if isinstance(queries, dict):
                for key in ("queries", "search_queries", "results"):
                    if isinstance(queries.get(key), list):
                        return queries[key][:depth]
        except Exception as e:
            logger.warning(f"[ResearcherAgent] Query expansion failed: {e}")
        return [query]  # fallback to original

    async def _synthesise(
        self,
        query: str,
        search_results: list[dict[str, Any]],
        scraped: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Synthesise all collected information into a structured report."""

        # Build sources context
        sources_text = self._format_sources(search_results, scraped)

        response = await self.llm.complete(
            system=RESEARCHER_SYSTEM_PROMPT,
            user=(
                f"Research Query: {query}\n\n"
                f"Collected Sources:\n{sources_text}\n\n"
                "Please synthesise these findings into a comprehensive research report."
            ),
            temperature=0.2,
        )

        # Extract numbered sources
        source_list = []
        for i, r in enumerate(search_results[:10], 1):
            source_list.append({
                "index": i,
                "title": r.get("title", f"Source {i}"),
                "url":   r.get("url", ""),
                "snippet": r.get("snippet", ""),
            })

        return {
            "full_text":    response,
            "sources":      source_list,
            "source_count": len(source_list),
            "scraped_count": len(scraped),
        }

    def _format_sources(
        self,
        search_results: list[dict[str, Any]],
        scraped: list[dict[str, Any]],
    ) -> str:
        lines = []

        # Search snippets
        if search_results:
            lines.append("=== Search Results ===")
            for i, r in enumerate(search_results[:12], 1):
                lines.append(
                    f"[{i}] {r.get('title', 'N/A')}\n"
                    f"    URL: {r.get('url', '')}\n"
                    f"    {r.get('snippet', '')[:300]}\n"
                )

        # Deep-scraped content
        if scraped:
            lines.append("\n=== Full Page Content ===")
            for item in scraped[:4]:
                lines.append(
                    f"Source: {item.get('title', item['url'])}\n"
                    f"URL: {item['url']}\n"
                    f"Content:\n{item['content'][:1500]}\n---\n"
                )

        return "\n".join(lines) if lines else "No sources collected."
