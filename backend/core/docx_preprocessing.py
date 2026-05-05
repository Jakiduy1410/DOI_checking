# docx_preprocessing.py
from __future__ import annotations

import re

from core.pdf_preprocessing import clean_parts

PLOS_PATTERN_1 = re.compile(r"^\s*(?:\*\*)?1\.(?:\*\*)?\s+", re.MULTILINE)
IEEE_PATTERN_1 = re.compile(r"^\s*(?:-\s*|\*\*\s*)*\\?\[1\\?\]", re.MULTILINE)
PLOS_PATTERN_N = re.compile(r"^\s*(?:\*\*)?\d+\.(?:\*\*)?\s+", re.MULTILINE)
IEEE_PATTERN_N = re.compile(r"^\s*(?:-\s*|\*\*\s*)*\\?\[\d+\\?\]", re.MULTILINE)


def detect_format(ref_data: str) -> str:
    if PLOS_PATTERN_1.search(ref_data):
        return "plos"
    if IEEE_PATTERN_1.search(ref_data):
        return "ieee"

    if len(PLOS_PATTERN_N.findall(ref_data)) > 2:
        return "plos"
    if len(IEEE_PATTERN_N.findall(ref_data)) > 2:
        return "ieee"

    if re.search(r"^\s*-\s+[A-Z]", ref_data, re.MULTILINE):
        return "dash_newline"
    if " - " in ref_data and len(ref_data.splitlines()) < 5:
        return "apa_inline"
    return "author_year"


def get_docx_references(md_content: str, source_name: str = "Tài liệu") -> tuple[list[str], str]:
    md_content = re.sub(r"!\[.*?\]\(.*?\)", "", md_content)
    ref_pattern = r"(?im)^[\#\*\_\s]*\**\_*(?:References?|Bibliography|Tài liệu tham khảo|REFERENCES)\_*\**[\:\*\_\s]*$"
    ref_location = re.search(ref_pattern, md_content)

    found_heading = bool(ref_location)
    ref_data = md_content[ref_location.end():] if found_heading else md_content

    if not found_heading:
        print(f"[!] Khong tim thay muc References trong: {source_name}. Dang fallback lay toan bo noi dung.")
    else:
        ref_data = re.split(r"(?m)^(?:\#+\s+.+|\*\*[A-Z][^\n\.]{2,80}\*\*)\s*$", ref_data, maxsplit=1)[0]
        ref_data = re.split(r"(?m)^\s*(?:Figure|Table|Appendix|Phụ lục)\s+\d+", ref_data, maxsplit=1)[0]

    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", ref_data)
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    text = text.replace("\\", "")
    text = re.sub(r"-\n\s*", "", text)

    fmt = detect_format(text)
    lines = text.split("\n")
    healed_lines: list[str] = []
    blank_lines = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
            continue

        is_start = False
        if not healed_lines:
            is_start = True
        else:
            prev_ref = healed_lines[-1]
            if fmt == "plos" and re.match(r"^\s*\d+\.\s+", stripped):
                is_start = True
            elif fmt == "ieee" and re.match(r"^\s*(?:-\s*)?\[\d+\]", stripped):
                is_start = True
            elif fmt == "dash_newline" and re.match(r"^\s*-\s+[A-Z]", stripped):
                is_start = True
            elif fmt == "author_year":
                if re.match(r"^\s*(?:https?://|doi:|www\.)", stripped):
                    is_start = False
                elif blank_lines > 0 or re.match(r"^[A-Z][^\n\d(]+?\(\d{4}[a-z]?\)", stripped):
                    if prev_ref.endswith((",", " and", " &", "-", "–", "et al.")) or re.match(r"^([a-z]|\(|http|doi|www|\d+)", stripped):
                        is_start = False
                    else:
                        is_start = True
                else:
                    is_start = False

        if is_start:
            healed_lines.append(stripped)
        else:
            healed_lines[-1] += " " + stripped

        blank_lines = 0

    if fmt == "apa_inline":
        ref_data_joined = " ".join(healed_lines)
        healed_lines = re.split(r"\s+-\s+(?=[A-Z][a-z])", ref_data_joined)

    clean_parts_list = clean_parts(healed_lines)
    print(f"[{source_name.encode('ascii', 'ignore').decode()}] format={fmt}  refs={len(clean_parts_list)}")

    return (clean_parts_list, fmt)