from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytesseract
from docx import Document as DocxDocument
from PIL import Image
from pdf2image import convert_from_bytes
from pptx import Presentation as PptPresentation
from pydantic import BaseModel


class FileExtractionError(Exception):
    """Raised when an uploaded file cannot be extracted."""


class ExtractorResponse(BaseModel):
    file_name: str
    file_type: str
    extracted_text: str


class FileTextExtractor:
    SUPPORTED_FORMATS = {
        "json": "json",
        "txt": "txt",
        "pdf": "pdf",
        "doc": "doc",
        "docx": "docx",
        "ppt": "ppt",
        "pptx": "pptx",
        "jpg": "image",
        "jpeg": "image",
        "png": "image",
    }

    def __init__(self) -> None:
        self.tessdata_dir = Path(__file__).resolve().parents[1] / "tessdata"
        self.ocr_config = f'--tessdata-dir "{self.tessdata_dir}"'

    def detect_format(self, file_name: str, selected_format: str | None = None) -> str:
        name = (file_name or "").lower().strip()
        extension = Path(name).suffix.lstrip(".")
        lookup = (selected_format or extension).lower().strip()
        if lookup in {"doc", "docx"}:
            return "docx"
        if lookup in {"ppt", "pptx"}:
            return "pptx"
        if lookup == "jpeg":
            return "jpg"
        if lookup not in self.SUPPORTED_FORMATS:
            raise FileExtractionError(
                f"Unsupported file format '{lookup}'. Supported: {', '.join(sorted(self.SUPPORTED_FORMATS))}."
            )
        return lookup

    async def extract(self, file_name: str, file_bytes: bytes, selected_format: str | None = None) -> ExtractorResponse:
        file_type = self.detect_format(file_name, selected_format)
        text = self._dispatch(file_type, file_bytes)
        return ExtractorResponse(file_name=file_name, file_type=file_type, extracted_text=text)

    def _dispatch(self, file_type: str, file_bytes: bytes) -> str:
        if file_type == "json":
            return self.extract_json(file_bytes)
        if file_type == "txt":
            return self.extract_txt(file_bytes)
        if file_type == "pdf":
            return self.extract_pdf(file_bytes)
        if file_type == "docx":
            return self.extract_doc(file_bytes)
        if file_type == "pptx":
            return self.extract_ppt(file_bytes)
        if file_type == "jpg":
            return self.extract_jpg(file_bytes)
        if file_type == "png":
            return self.extract_png(file_bytes)
        raise FileExtractionError(f"No extractor implemented for '{file_type}'.")

    def extract_json(self, file_bytes: bytes) -> str:
        text = file_bytes.decode("utf-8")
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2, ensure_ascii=False)

    def extract_txt(self, file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8")

    def extract_pdf(self, file_bytes: bytes) -> str:
        images = convert_from_bytes(file_bytes)
        text_chunks: list[str] = []
        for page_number, page in enumerate(images, start=1):
            page_text = pytesseract.image_to_string(page, lang="spa", config=self.ocr_config)
            text_chunks.append(f"\n--- Page {page_number} ---\n{page_text.strip()}")
        return "\n".join(text_chunks).strip()

    def extract_doc(self, file_bytes: bytes) -> str:
        try:
            document = DocxDocument(io.BytesIO(file_bytes))
        except Exception as exc:
            raise FileExtractionError(f"Unable to read DOC file: {exc}") from exc

        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        tables = []
        for table in document.tables:
            for row in table.rows:
                tables.append(" | ".join(cell.text for cell in row.cells))

        scanned_chunks: list[str] = []
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                for member_name in archive.namelist():
                    if member_name.startswith("word/media/") and member_name.lower().endswith((".png", ".jpg", ".jpeg")):
                        image_bytes = archive.read(member_name)
                        scanned_chunks.append(self.ocr_image_bytes(image_bytes))
        except Exception:
            scanned_chunks = []

        combined = paragraphs + tables + [chunk for chunk in scanned_chunks if chunk.strip()]
        return "\n".join(combined).strip()

    def extract_ppt(self, file_bytes: bytes) -> str:
        try:
            presentation = PptPresentation(io.BytesIO(file_bytes))
        except Exception as exc:
            raise FileExtractionError(f"Unable to read PPT file: {exc}") from exc

        text_chunks: list[str] = []
        for slide_number, slide in enumerate(presentation.slides, start=1):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    shape_text = shape.text.strip()
                    if shape_text:
                        slide_text.append(shape_text)

                if hasattr(shape, "image"):
                    try:
                        image_text = self.ocr_image_bytes(shape.image.blob)
                        if image_text.strip():
                            slide_text.append(image_text.strip())
                    except Exception:
                        pass

            if slide_text:
                text_chunks.append(f"\n--- Slide {slide_number} ---\n" + "\n".join(slide_text))
        return "\n".join(text_chunks).strip()

    def extract_jpg(self, file_bytes: bytes) -> str:
        return self.extract_image(file_bytes)

    def extract_png(self, file_bytes: bytes) -> str:
        return self.extract_image(file_bytes)

    def ocr_image_bytes(self, file_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(file_bytes))
        except Exception as exc:
            raise FileExtractionError(f"Unable to open image file: {exc}") from exc
        return pytesseract.image_to_string(image, lang="spa", config=self.ocr_config)

    def extract_image(self, file_bytes: bytes) -> str:
        return self.ocr_image_bytes(file_bytes)


__all__ = ["FileTextExtractor", "FileExtractionError", "ExtractorResponse"]
