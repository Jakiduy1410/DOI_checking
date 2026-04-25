import os
import re
import pymupdf
import pymupdf4llm
from markitdown import MarkItDown

md_converter = MarkItDown()

def normalize_docx_md(raw_md: str) -> str:
    # MarkItDown sản xuất base64 images, chúng ta cần xóa chúng để tránh làm loãng text
    text = re.sub(r'!\[.*?\]\(data:image\/.*?\)', '', raw_md)
    # Xóa cả các chuỗi base64 rời nếu có
    text = re.sub(r'data:image\/[^;]+;base64,[A-Za-z0-9+/=\s\n]+?[\)\]\s]', '', text)
    
    text = text.replace('\\', '')
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def convert_to_md(file_path: str) -> str:

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File không tồn tại: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        doc = pymupdf.open(file_path)
        md_text = pymupdf4llm.to_markdown(doc)
        doc.close()
        return md_text

    elif ext == '.docx':
        result = md_converter.convert(file_path)
        return normalize_docx_md(result.text_content)

    elif ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    elif ext == '.doc':
        raise ValueError("Định dạng .doc cũ không được hỗ trợ. Vui lòng Save As sang .docx hoặc .pdf để tiếp tục.")

    else:
        raise ValueError(f"Định dạng {ext} không được hỗ trợ.")
