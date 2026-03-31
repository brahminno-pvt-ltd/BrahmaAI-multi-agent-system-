"""
BrahmaAI File Upload API
Handles file uploads for the file_reader tool.
"""

import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from backend.tools.file_reader import FileReaderTool

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = Path("./data/uploads")
ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".md", ".json"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

_file_reader = FileReaderTool()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """
    Upload a file (PDF, CSV, TXT, MD, JSON) and extract its text content.
    Returns the extracted text and a temporary file path for agent use.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read and size-check
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024}MB",
        )

    # Save to upload dir
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())[:8]
    safe_name = f"{file_id}_{Path(file.filename).stem[:40]}{ext}"
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"[UploadAPI] Saved: {file_path} ({len(content)} bytes)")

    # Extract content immediately
    result = await _file_reader.execute(
        file_path=str(file_path),
        max_chars=8000,
    )

    return JSONResponse({
        "status": "success",
        "file_id": file_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "file_size": len(content),
        "file_type": ext,
        "extraction": result,
        "agent_prompt": f"Read the uploaded file at {file_path} and analyze its contents",
    })


@router.get("/uploads")
async def list_uploads() -> JSONResponse:
    """List recently uploaded files."""
    if not UPLOAD_DIR.exists():
        return JSONResponse({"files": [], "count": 0})

    files = []
    for f in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
        if f.is_file():
            stat = f.stat()
            files.append({
                "filename": f.name,
                "path": str(f),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })

    return JSONResponse({"files": files, "count": len(files)})


@router.delete("/uploads/{filename}")
async def delete_upload(filename: str) -> JSONResponse:
    """Delete an uploaded file."""
    # Security: prevent path traversal
    safe_filename = Path(filename).name
    file_path = UPLOAD_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not str(file_path).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid path")

    os.unlink(file_path)
    return JSONResponse({"status": "deleted", "filename": safe_filename})
