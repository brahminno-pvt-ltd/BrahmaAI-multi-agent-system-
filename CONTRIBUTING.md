# Contributing to BrahmaAI

Thank you for your interest in contributing to BrahmaAI! This guide will help you get started.

---

## Development Setup

```bash
git clone https://github.com/yourname/brahmaai.git
cd brahmaai

# Setup environment
cp .env.example .env
# Edit .env with your API keys (optional — demo mode works without them)

# Backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

---

## Running Tests

```bash
# Backend tests (all)
cd backend && pytest tests/ -v

# Specific test class
pytest tests/test_all.py::TestCodeExecutorTool -v

# With coverage
pytest tests/ --cov=backend --cov-report=term-missing
```

---

## Code Style

### Python
- **Formatter:** `ruff format .`
- **Linter:** `ruff check .`
- **Type checker:** `mypy . --ignore-missing-imports`
- All public functions must have docstrings
- All function parameters must have type hints
- Return types must be declared

```python
# ✅ Good
async def plan(self, goal: str, memory_context: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Generate a structured execution plan for the given goal."""
    ...

# ❌ Bad
async def plan(self, goal, memory_context=None):
    ...
```

### TypeScript
- **Linter:** `npm run lint`
- **Type checker:** `npx tsc --noEmit`
- Use explicit types, avoid `any`
- React components: named exports for utilities, default export for pages

---

## Adding a New Tool

1. Create `backend/tools/my_tool.py`:

```python
from backend.tools.registry import BaseTool
from typing import Any

class MyTool(BaseTool):
    name = "my_tool"
    description = "One-sentence description of what this tool does"
    args = {
        "input": "str: Description of the input parameter",
    }

    async def execute(self, input: str, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool and return a structured result."""
        try:
            result = do_something(input)
            return {
                "status": "success",
                "output": str(result),
                # Add tool-specific fields as needed
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "output": f"Failed: {e}",
            }
```

2. Register in `backend/tools/registry.py`:

```python
from backend.tools.my_tool import MyTool
# In _register_default_tools():
registry.register_class(MyTool)
```

3. Add tests in `backend/tests/test_all.py`:

```python
class TestMyTool:
    @pytest.mark.asyncio
    async def test_execute_success(self):
        from backend.tools.my_tool import MyTool
        tool = MyTool()
        result = await tool.execute(input="test")
        assert result["status"] == "success"
        assert "output" in result
```

---

## Pull Request Process

1. Fork the repo and create a branch: `git checkout -b feature/my-feature`
2. Make your changes with tests
3. Run the full test suite: `pytest tests/ -v`
4. Run linters: `ruff check . && ruff format --check .`
5. Commit with conventional commits: `feat: add stock price tool`
6. Open a PR with a clear description

### Commit Message Format

```
feat: add weather tool using Open-Meteo API
fix: handle empty FAISS index on first startup
docs: add architecture diagram to README
test: add integration tests for orchestrator
refactor: extract LLM retry logic to separate function
chore: update dependencies
```

---

## Reporting Issues

Please include:
- Python/Node version
- Full error message and stack trace
- Steps to reproduce
- Expected vs. actual behavior
- Relevant `.env` settings (without API keys)

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
