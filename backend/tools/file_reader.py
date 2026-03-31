"""
BrahmaAI File Reader Tool
Reads and extracts content from PDF, CSV, and TXT files.
"""

import logging
import os
from typing import Any

from backend.tools.registry import BaseTool

logger = logging.getLogger(__name__)


class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Read and extract content from PDF, CSV, or TXT files"
    args = {
        "file_path": "str: Path to the file to read",
        "max_chars": "int: Maximum characters to extract (default: 5000)",
    }

    async def execute(
        self,
        file_path: str,
        max_chars: int = 5000,
        **kwargs: Any,
    ) -> dict[str, Any]:
        logger.info(f"[FileReaderTool] Reading: {file_path}")

        if not os.path.exists(file_path):
            return {
                "status": "error",
                "error": f"File not found: {file_path}",
                "output": f"File not found: {file_path}",
            }

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".pdf":
                content = self._read_pdf(file_path, max_chars)
            elif ext == ".csv":
                content = self._read_csv(file_path, max_chars)
            elif ext in (".txt", ".md", ".json", ".yaml", ".yml"):
                content = self._read_text(file_path, max_chars)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported file type: {ext}",
                    "output": f"Cannot read {ext} files. Supported: PDF, CSV, TXT, MD, JSON",
                }

            return {
                "status": "success",
                "file_path": file_path,
                "file_type": ext,
                "output": content,
                "char_count": len(content),
            }

        except Exception as e:
            logger.error(f"[FileReaderTool] Error reading {file_path}: {e}")
            return {
                "status": "error",
                "file_path": file_path,
                "error": str(e),
                "output": f"Error reading file: {e}",
            }

    def _read_pdf(self, path: str, max_chars: int) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            pages = []
            total = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)
                total += len(text)
                if total >= max_chars:
                    break
            full_text = "\n".join(pages)
            return full_text[:max_chars]
        except ImportError:
            return f"[PDF reading requires pypdf: pip install pypdf]\nFile: {path}"

    def _read_csv(self, path: str, max_chars: int) -> str:
        import csv
        lines = []
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                lines.append(", ".join(row))
                if sum(len(l) for l in lines) >= max_chars:
                    lines.append(f"... (truncated at row {i})")
                    break
        return "\n".join(lines)

    def _read_text(self, path: str, max_chars: int) -> str:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
