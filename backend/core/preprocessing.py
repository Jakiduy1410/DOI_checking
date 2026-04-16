import re
import pymupdf
import pymupdf4llm

def get_references(path: str) -> tuple[list[str], str]:
    doc = pymupdf.open(path)
    md = pymupdf4llm.to_markdown(doc)
    ref_location = re.search('(?i)^[\\#\\*\\_\\s]*References?[\\:\\*\\_\\s]*\\n', md, flags=re.MULTILINE)
    if not ref_location:
        print(f'[!] Không tìm thấy mục References trong: {path}')
        return ([], 'unknown')
    ref_data = md[ref_location.end():]
    ref_data = re.sub('\\|', '', ref_data)
    ref_data = re.sub('\\*\\*==> picture.*?<==\\*\\*', '', ref_data)
    ref_data = re.sub('PLOS ONE.*?(?=\\n|$)', '', ref_data)
    fmt = detect_format(ref_data)
    refs = split_refs(ref_data, fmt)
    print(f'[{path}] format={fmt}  refs={len(refs)}')
    return (refs, fmt)
    
def detect_format(ref_data: str) -> str:
    if re.search('^\\s*\\*\\*\\d+\\.\\*\\*', ref_data, re.MULTILINE):
        return 'plos'
    if re.search('^\\s*(?:-\\s*|\\*\\*\\s*)*\\\\?\\[\\d+\\\\?\\]', ref_data, re.MULTILINE):
        return 'ieee'
    if re.search('^\\s*-\\s+[A-Z]', ref_data, re.MULTILINE):
        return 'dash_newline'
    if ' - ' in ref_data and len(ref_data.splitlines()) < 5:
        return 'apa_inline'
    return 'author_year'

def split_refs(ref_data: str, fmt: str) -> list[str]:
    ref_data = ref_data.strip()
    if fmt == 'plos':
        parts = re.split('(?=\\*\\*\\d+\\.\\*\\*)', ref_data)
    elif fmt == 'ieee':
        parts = re.split('(?=\\[\\d+\\])', ref_data)
    elif fmt == 'dash_newline':
        parts = re.split('\\n+(?=-\\s+[A-Z])', ref_data)
    elif fmt == 'apa_inline':
        parts = re.split('\\s+-\\s+(?=[A-Z][a-z])', ref_data)
    else:
        parts = re.split('\\n(?=[A-Z][a-z]+\\s+[A-Z])', ref_data)
    return clean_parts(parts)

def clean_parts(parts: list[str]) -> list[str]:
    clean = []
    for p in parts:
        p = p.strip().split('\n\n')[0]
        p = p.replace('\n', ' ').strip()
        p = re.sub('\\*\\*\\d+\\.\\*\\*', '', p)
        p = re.sub('^\\[\\d+\\]\\s*', '', p)
        p = re.sub('^-\\s*', '', p)
        p = re.sub('\\s+', ' ', p).strip()
        if p and p != '-':
            clean.append(p)
    return clean
