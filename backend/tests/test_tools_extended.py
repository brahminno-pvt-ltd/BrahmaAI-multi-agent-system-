"""
BrahmaAI Web Scraper Tool Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestWebScraperTool:
    @pytest.mark.asyncio
    async def test_scrape_returns_error_on_network_failure(self):
        from backend.tools.web_scraper import WebScraperTool
        tool = WebScraperTool()

        with patch("backend.tools.web_scraper.httpx") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_httpx.AsyncClient.return_value = mock_client

            result = await tool.execute(url="http://nonexistent.invalid")

        assert result["status"] == "error"
        assert "error" in result

    def test_html_extraction_removes_scripts(self):
        from backend.tools.web_scraper import WebScraperTool
        tool = WebScraperTool()
        html = """
        <html><body>
            <script>alert('xss')</script>
            <nav>Skip nav</nav>
            <main><p>Real content here</p></main>
            <footer>Footer junk</footer>
        </body></html>
        """
        text = tool._extract_text_from_html(html)
        assert "Real content here" in text
        assert "alert" not in text

    def test_html_extraction_collapses_whitespace(self):
        from backend.tools.web_scraper import WebScraperTool
        tool = WebScraperTool()
        html = "<p>Line 1</p>\n\n\n\n\n<p>Line 2</p>"
        text = tool._extract_text_from_html(html)
        # Should not have 3+ consecutive newlines
        assert "\n\n\n" not in text


class TestToolRegistry:
    def test_default_tools_all_registered(self):
        from backend.tools.registry import get_tool_registry
        registry = get_tool_registry()
        tools = registry.list_tools()
        expected = ["web_search", "web_scraper", "file_reader",
                    "code_executor", "email_tool", "calendar_tool"]
        for name in expected:
            assert name in tools, f"Expected tool not registered: {name}"

    def test_tool_schema_has_required_fields(self):
        from backend.tools.registry import get_tool_registry
        registry = get_tool_registry()
        for name, schema in registry.list_tools().items():
            assert "name" in schema, f"{name} schema missing 'name'"
            assert "description" in schema, f"{name} schema missing 'description'"
            assert "args" in schema, f"{name} schema missing 'args'"
