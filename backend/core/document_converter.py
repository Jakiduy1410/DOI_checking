# document_converter.py
from __future__ import annotations

import os
import re
import sys
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pymupdf
import pymupdf4llm
import pytesseract
from pdf2image import convert_from_path
from markitdown import MarkItDown
from docx2pdf import convert as docx2pdf_convert

md_converter = MarkItDown()

_TEXT_SAMPLE_PAGES = 3
_TEXT_THRESHOLD = 100
_MAX_OCR_WORKERS = 8


def ocr_single_page(image) -> str:
    """OCR độc lập cho một trang ảnh."""
    return pytesseract.image_to_string(image, lang="eng+vie")


def normalize_docx_md(raw_md: str) -> str:
    text = re.sub(r"!\[.*?\]\(data:image\/.*?\)", "", raw_md)
    text = re.sub(r"data:image\/[^;]+;base64,[A-Za-z0-9+/=\s\n]+?(?=[\)\]\s]|$)", "", text)
    text = text.replace("\\", "")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pdf_has_text(doc) -> bool:
    sample_text = []
    limit = min(_TEXT_SAMPLE_PAGES, doc.page_count)
    for i in range(limit):
        sample_text.append(doc[i].get_text())
        if sum(len(chunk) for chunk in sample_text) > _TEXT_THRESHOLD:
            return True
    return False


def _ocr_images(images) -> list[str]:
    workers = min(os.cpu_count() or 4, _MAX_OCR_WORKERS)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(ocr_single_page, images))


def convert_to_md(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File không tồn tại: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        doc = pymupdf.open(file_path)
        try:
            if _pdf_has_text(doc):
                return pymupdf4llm.to_markdown(doc)
        finally:
            doc.close()

        print(f"[OCR] Phát hiện PDF Scan, đang khởi động Tesseract cho: {os.path.basename(file_path)}")
        images = convert_from_path(file_path)
        return "\n\n".join(_ocr_images(images))

    if ext == ".docx":
        result = md_converter.convert(file_path)
        return normalize_docx_md(result.text_content)

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    if ext == ".doc":
        raise ValueError("Định dạng .doc cũ không được hỗ trợ. Vui lòng Save As sang .docx hoặc .pdf để tiếp tục.")

    raise ValueError(f"Định dạng {ext} không được hỗ trợ.")


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool:
    try:
        target = Path(pdf_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        if sys.platform == "win32":
            docx2pdf_convert(docx_path, pdf_path)
        else:
            outdir = str(target.parent)
            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    outdir,
                    docx_path,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            generated_pdf = target.parent / (Path(docx_path).stem + ".pdf")
            if generated_pdf.exists() and generated_pdf != target:
                if target.exists():
                    target.unlink()
                generated_pdf.rename(target)

        return target.exists()
    except Exception as e:
        print(f"[!] Loi chuyen doi DOCX sang PDF: {e}")
        return False