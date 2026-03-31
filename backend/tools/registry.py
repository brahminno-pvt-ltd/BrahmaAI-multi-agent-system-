"""
BrahmaAI Tool Registry
Plugin-style registry for dynamically registering and dispatching tools.
"""

import logging
from typing import Any, Type

logger = logging.getLogger(__name__)


class BaseTool:
    """Abstract base class for all BrahmaAI tools."""

    name: str = ""
    description: str = ""
    args: dict[str, str] = {}

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with given arguments. Must return a dict."""
        raise NotImplementedError

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "args": self.args,
        }


class ToolRegistry:
    """
    Central registry for all available tools.
    Tools can be registered dynamically (plugin system).
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool
        logger.info(f"[ToolRegistry] Registered tool: {tool.name}")

    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool by class (instantiates it)."""
        instance = tool_class()
        self.register(instance)

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> dict[str, dict[str, Any]]:
        """List all registered tools with their schemas."""
        return {name: tool.schema() for name, tool in self._tools.items()}

    def all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())


# --- Singleton registry with all tools registered ---

_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_default_tools(_registry)
    return _registry


def _register_default_tools(registry: ToolRegistry) -> None:
    """Register all built-in tools."""
    from backend.tools.web_search import WebSearchTool
    from backend.tools.web_scraper import WebScraperTool
    from backend.tools.file_reader import FileReaderTool
    from backend.tools.code_executor import CodeExecutorTool
    from backend.tools.email_tool import EmailTool
    from backend.tools.calendar_tool import CalendarTool

    for tool_class in [
        WebSearchTool,
        WebScraperTool,
        FileReaderTool,
        CodeExecutorTool,
        EmailTool,
        CalendarTool,
    ]:
        try:
            registry.register_class(tool_class)
        except Exception as e:
            logger.error(f"Failed to register {tool_class.__name__}: {e}")
