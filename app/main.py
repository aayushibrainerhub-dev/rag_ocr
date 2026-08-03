from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from app.extractor import FileExtractionError, FileTextExtractor

app = FastAPI(title="OCR-RAG Extractor API")

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")
extractor = FileTextExtractor()


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(content=INDEX_HTML)


@app.post("/extract")
async def extract_text(
    file: UploadFile = File(...),
    file_type: str | None = Form(default=None),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file must be provided.")

    try:
        file_bytes = await file.read()
        response = await extractor.extract(file.filename, file_bytes, selected_format=file_type)
        return response.model_dump()
    except FileExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error while extracting text: {exc}") from exc
