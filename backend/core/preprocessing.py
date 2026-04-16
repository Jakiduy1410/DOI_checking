import re

def get_references(md_content: str, source_name: str = "Tài liệu") -> tuple[list[str], str]:
    ref_location = re.search(r'(?i)^[\#\*\_\s]*\**\_*References?\_*\**[\:\*\_\s]*$', md_content, flags=re.MULTILINE)
    if not ref_location:
        print(f'[!] Không tìm thấy mục References trong: {source_name}')
        return ([], 'unknown')
    ref_data = md_content[ref_location.end():]
    ref_data = re.sub('\\|', '', ref_data)
    ref_data = re.sub('\\*\\*==> picture.*?<==\\*\\*', '', ref_data)
    ref_data = re.sub('PLOS ONE.*?(?=\\n|$)', '', ref_data)
    fmt = detect_format(ref_data)
    refs = split_refs(ref_data, fmt)
    print(f'[{source_name}] format={fmt}  refs={len(refs)}')
    return (refs, fmt)
    
def detect_format(ref_data: str) -> str:
    if re.search(r'^\s*(?:\*\*)?\d+\.(?:\*\*)?\s+', ref_data, re.MULTILINE):
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
        if '**1.**' in ref_data or '**2.**' in ref_data:
            parts = re.split(r'(?=\*\*\d+\.\*\*)', ref_data)
        else:
            parts = re.split(r'(?m)^(?=\s*\d+\.\s+)', ref_data)
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
        p = p.strip()
        if '\n\n#' in p:
            p = p.split('\n\n#')[0]
        p = p.replace('\n', ' ').strip()
        p = re.sub(r'^\s*(?:\*\*)?\d+\.(?:\*\*)?\s*', '', p)
        p = re.sub(r'^\[\d+\]\s*', '', p)
        p = re.sub('^-\\s*', '', p)
        p = re.sub('\\s+', ' ', p).strip()
        
        # Sửa lỗi url bị tách dấu chấm ("*.*" hoặc "_._" hoặc khoảng trắng thừa xung quanh dấu chấm)
        p = re.sub(r'\s?[_*]\.[_*]\s?', '.', p)
        p = re.sub(r'(?i)(https?://[^\s]+)\s+([a-z0-9])', r'\1\2', p) # Sửa khoảng trắng ngẫu nhiên trong url
        
        # Sửa URL bị trùng lặp do DOCX
        p = re.sub(r'(https?://[^\s]+)\s+(?:\1|\[\1\]\(\1\))', r'\1', p)
        
        # Xóa các rác thừa ở cuối chuỗi
        p = re.sub(r'[\s\-"\']+$', '', p)  # dấu gạch ngang, nháy kép thừa
        p = re.sub(r'\s+\d+\s*/\s*\d+$', '', p) # Chỉ xóa chính xác số trang kiểu "11 / 11"
        
        if p and p != '-':
            clean.append(p)
    return clean
