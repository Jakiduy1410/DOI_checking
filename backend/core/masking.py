import re
from dataclasses import dataclass, field, asdict

@dataclass
class Reference:
    authors: str = ''
    year: str = ''
    title: str = ''
    doi: str = ''
    raw: str = ''
    is_web: bool = False

DOI_PATTERN = re.compile('(?:https?:\\/\\/.{0,5}doi\\.org\\/|doi(?![a-z]):?\\s*)(10\\.\\d{4,9}\\s*\\/\\s*\\S+(?:\\s+(?![A-Z][a-z])\\S+)*)', re.IGNORECASE)

ACADEMIC_DOMAINS = {'doi.org', 'arxiv.org', 'biorxiv.org', 'medrxiv.org', 'nature.com', 'springer.com', 'sciencedirect.com', 'wiley.com', 'ieee.org', 'acm.org', 'nih.gov', 'ncbi.nlm.nih.gov', 'pubmed.ncbi.nlm.nih.gov', 'plos.org', 'jstor.org', 'tandfonline.com', 'sagepub.com', 'cambridge.org', 'oxford.org', 'oup.com', 'elsevier.com', 'researchgate.net', 'semanticscholar.org', 'scopus.com', 'webofscience.com', 'ssrn.com', 'aclweb.org', 'frontiersin.org', 'mdpi.com', 'biomedcentral.com', 'hindawi.com', 'ams.org', 'aps.org', 'iop.org', 'rsc.org', 'pnas.org', 'science.org', 'cell.com', 'thelancet.com', 'bmj.com'}

# [FIX-1] Nhận diện tên tạp chí/hội nghị/preprint để không lấy nhầm làm title
VENUE_PATTERN = re.compile(
    r'(?:^|\.\s+)'                            # Bắt đầu chuỗi hoặc sau dấu chấm
    r'('
    r'[Ii]n\s+_[^_]+_'                        # In _Venue Name_
    r'|[Ii]n\s+[Pp]roceedings\b.*'            # In Proceedings of...
    r'|[Pp]roceedings\s+of\b.*'               # Proceedings of...
    r'|_[^_]*(?:[Pp]roceedings|[Jj]ournal|[Cc]onference|[Ss]ymposium|[Ww]orkshop|[Tt]ransactions|[Aa]rchive|[Aa]dvances|[Pp]reprint|[Rr]eview)[^_]*_'  # _Venue in italics_
    r'|arXiv\s+preprint\b.*'                  # arXiv preprint arXiv:XXXX
    r'|_Preprint_.*'                           # _Preprint_, arXiv:XXXX
    r'|_URL:.*'                                # _URL: ..._
    r')',
    re.IGNORECASE
)

# [FIX-2] Xóa rác web/github dính vào cuối title
WEB_JUNK_PATTERN = re.compile(
    r'\s*(?:https?://|www\.)\S*.*$'            # URL đầy đủ
    r'|\s*[\w.-]+\.(?:com|org|net|edu|gov|io|html)(?:/\S*)?.*$'  # domain trần (nytimes.com/...)
    r'|\s+\d{4,}$',                            # mã issue cuối chuỗi (67513, 84018...)
    re.IGNORECASE
)

def preprocess_ref(text: str, fmt: str) -> str:
    if fmt == 'plos':
        text = re.sub('Available:\\s*https?://\\S+', '', text)
        text = re.sub('Accessed\\s*\\d*\\s*\\w+\\s+\\d{4}\\.?', '', text)
    text = re.sub('`(doi:[^`]+)`', lambda x: x.group(1).replace(' ', ''), text)
    text = re.sub('`(https?://[^`]+)`', lambda x: x.group(1).replace(' ', ''), text)
    return re.sub('\\s+', ' ', text).strip()

def extract_year(text: str) -> tuple[str, str]:
    m = re.search('\\((\\d{4})[a-z]?\\)', text)
    if m:
        return (m.group(1), text[:m.start()] + '[YEAR]' + text[m.end():])
    m = re.search('(?<![/\\d.])(?:19|20)\\d{2}(?![/\\d])', text)
    if m:
        return (m.group(0), text[:m.start()] + '[YEAR]' + text[m.end():])
    return ('', text)

def extract_doi(text: str) -> tuple[str, str]:
    m = DOI_PATTERN.search(text)
    if m:
        raw_doi = m.group(0)
        clean_doi = raw_doi.replace(' ', '').replace('\n', '').rstrip('.,')
        clean_doi = re.split('PMID:|PMCID:', clean_doi, flags=re.IGNORECASE)[0]
        return (clean_doi, text.replace(raw_doi, '', 1))
    return ('', text)

def clean_title(title: str) -> str:
    # [FIX-1] Cắt title trước khi gặp venue/journal/preprint
    vm = VENUE_PATTERN.search(title)
    if vm:
        candidate = title[:vm.start()].rstrip(' .,;')
        if len(candidate) >= 10:
            title = candidate

    # [FIX-2] Xóa URL, domain trần, mã issue number cuối chuỗi
    title = WEB_JUNK_PATTERN.sub('', title).strip(' .,-')
    return title

def extract_title_authors(text: str, fmt: str) -> tuple[str, str]:
    # --- Nhánh 1: title nằm trong dấu ngoặc kép ---
    q = re.search('[\u201c"](.*?)[\u201d"]', text)
    if q:
        raw_authors = text[:q.start()].replace('[YEAR]', '').strip(' .,-')
        quoted_title = clean_title(q.group(1).strip(' .,'))

        # [FIX-3] Kiểm tra PLOS: nếu phần "authors" chứa từ dài không phải tên người
        # (ví dụ: "Lingenfelter K Science Meets Fiction") thì tách lại bằng pattern tên
        if fmt == 'plos' and raw_authors:
            non_name_words = [w for w in raw_authors.split()
                              if len(w) > 2 and w[0].isupper() and w not in ('The', 'And', 'Van', 'Von', 'Der', 'Del', 'De', 'La')]
            name_initials = [w for w in raw_authors.split() if len(w) <= 2 and w[0].isupper()]
            # Nếu có nhiều từ dài hơn số initials -> khả năng cao title bị nuốt vào authors
            if len(non_name_words) > len(name_initials) + 2:
                am = re.match(
                    r'^((?:[A-Z][a-z]+(?:\s+[A-Z]\.?){0,3}(?:\s*,\s*)?)+?)\s+'
                    r'([A-Z][a-z]{2,}.*)',
                    raw_authors
                )
                if am:
                    real_authors = am.group(1).strip(' .,-')
                    full_title = am.group(2).strip() + ' ' + q.group(0) + text[q.end():].split('.')[0]
                    return (real_authors, clean_title(full_title.strip(' .,')))

        return (raw_authors, quoted_title)

    # --- Nhánh 2: có năm xuất bản -> tách authors|title theo [YEAR] ---
    if '[YEAR]' in text:
        before, after = text.split('[YEAR]', 1)
        authors = before.strip(' .,()')
        after = re.sub('^[\\s.),\\"]*', '', after).strip()
        if fmt == 'plos':
            dot = re.split('\\.\\s+', after, maxsplit=1)
            return (authors, clean_title(dot[0].strip()))
        # Tìm italic: _Content_
        it = re.search('_([^_]{5,120})_', after)
        if it:
            italic_text = it.group(1).strip('.')
            # [FIX-1] Nếu italic là venue/preprint -> lấy text TRƯỚC nó làm title
            is_venue = re.search(
                r'(?:Proceedings|Journal|Conference|Symposium|Workshop|'
                r'Transactions|Advances|arXiv\s+preprint|Preprint|'
                r'IEEE|ACM|USENIX|SIGARCH|SIGSAC|SIGPLAN)',
                italic_text, re.IGNORECASE
            )
            if is_venue:
                # Text trước "In _Venue_" hoặc ". _Venue_" chính là title
                title_part = after[:it.start()].rstrip(' .,;')
                # Xóa "In" hoặc "In:" ở cuối nếu có
                title_part = re.sub(r'\s+[Ii]n\s*:?\s*$', '', title_part).strip(' .,')
                if len(title_part) >= 5:
                    return (authors, clean_title(title_part))
            
            # Nếu KHÔNG phải venue từ khóa, nhưng phần text TRƯỚC italic đủ dài (>15 ký tự), 
            # thì text đó chính là title, còn italic là tên tạp chí (APA style)
            before_italic = after[:it.start()].rstrip(' .,;')
            before_italic = re.sub(r'^["\u201c](.*?)["\u201d]$', r'\1', before_italic.strip()).strip()
            if len(before_italic) >= 15:
                # Xóa "In" hoặc "In:" ở cuối nếu có
                before_italic = re.sub(r'\s+[Ii]n\s*:?\s*$', '', before_italic).strip(' .,')
                return (authors, clean_title(before_italic))
                
            # Italic KHÔNG phải venue và không có text phía trước -> dùng italic làm title như cũ
            return (authors, clean_title(italic_text))
        dot = re.split('\\.\\s+', after, maxsplit=1)
        return (authors, clean_title(dot[0].strip()))

    # --- Nhánh 3 (PLOS): pattern tên riêng ---
    if fmt == 'plos':
        m = re.match('^((?:[A-Z][a-z]+(?:-[A-Z][a-z]+)?\\s+(?:[A-Z]{1,3}\\s*)(?:,\\s*)?)+?)\\s+([A-Z].*)', text)
        if m:
            return (m.group(1).strip(' ,'), clean_title(m.group(2).strip()))
        return ('', clean_title(text.strip(' .')))

    # --- [FIX-3] Không có năm: tách ranh giới tác giả - tiêu đề ---
    # Pattern: "Lastname I, Lastname I" rồi chuyển sang câu bình thường
    am = re.match(
        r'^((?:[A-Z][a-z]+(?:\s+[A-Z]\.?){0,3}(?:\s*,\s*|\s+(?:and|&)\s+))*'
        r'[A-Z][a-z]+(?:\s+[A-Z]\.?){0,3})'
        r'[\s.,]+'
        r'([A-Z][a-z]{2,}.*)',
        text
    )
    if am:
        authors = am.group(1).strip(' .,-')
        title = clean_title(am.group(2).strip(' .'))
        return (authors, title)

    # --- [FIX-4] Fallback: lấy text trước URL/DOI làm title tạm ---
    url_pos = re.search(r'https?://|doi[:\s]', text, re.IGNORECASE)
    if url_pos:
        fallback = text[:url_pos.start()].strip(' .,-')
        if fallback:
            return ('', clean_title(fallback))
    return ('', clean_title(text.strip(' .,-')))

def is_website(text: str, doi: str) -> bool:
    if doi:
        return False
        
    clean_text = re.sub(r'\s*\.\s*', '.', text)
    
    urls = re.findall('https?://([^\\s/,)]+)', clean_text)
    if not urls:
        return False
    for domain in urls:
        domain = domain.lower().rstrip('.')
        if any((domain == d or domain.endswith('.' + d) for d in ACADEMIC_DOMAINS)):
            return False
    return True

def masking(refs: list[str], fmt: str) -> list[Reference]:
    results = []
    for raw in refs:
        raw = re.sub(r'\s*_\._\s*', '.', raw)
        raw = re.sub(r'(https?)\s*:\s*/\s*/', r'\1://', raw) 
        raw = re.sub(r'\s*_[~∼]_\s*', '~', raw)             
        raw = re.sub(r'(?<=[a-zA-Z0-9])\s+(?=/)|(?<=/)\s+(?=[a-zA-Z0-9])', '', raw)
        
        text = preprocess_ref(raw, fmt)
        year, text = extract_year(text)
        doi, text = extract_doi(text)
        authors, title = extract_title_authors(text, fmt)
        web = is_website(raw, doi)
        tmp = Reference(authors=authors, year=year, title=title, doi=doi, raw=raw, is_web=web)
        results.append(tmp)
    return results
