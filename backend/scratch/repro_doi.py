
import re
from dataclasses import dataclass

@dataclass
class Reference:
    authors: str = ''
    year: str = ''
    title: str = ''
    doi: str = ''
    raw: str = ''
    is_web: bool = False

DOI_PATTERN = re.compile(r'(?:https?://(?:[a-zA-Z0-9-]+\.)?doi\.org/|doi:?\s*)(10\.\d{4,9}\s*/\s*\S+(?:\s+(?![A-Z][a-z])\S+)*)', re.IGNORECASE)

def preprocess_ref(text: str, fmt: str) -> str:
    if fmt == 'plos':
        # [FIX] Tránh xóa nhầm DOI URL khi ở format PLOS
        text = re.sub(r'Available:\s*https?://(?!(?:dx\.)?doi\.org/)\S+', '', text)
        text = re.sub('Accessed\\s*\\d*\\s*\\w+\\s+\\d{4}\\.?', '', text)
    text = re.sub('`(doi:[^`]+)`', lambda x: x.group(1).replace(' ', ''), text)
    text = re.sub('`(https?://[^`]+)`', lambda x: x.group(1).replace(' ', ''), text)
    return re.sub('\\s+', ' ', text).strip()

def extract_doi(text: str) -> tuple[str, str]:
    m = DOI_PATTERN.search(text)
    if m:
        full_match = m.group(0)
        raw_doi = m.group(1)
        # [FIX] Xóa thêm dấu ngoặc dính ở cuối DOI
        clean_doi = raw_doi.replace(' ', '').replace('\n', '').rstrip('.,)]')
        clean_doi = re.split('PMID:|PMCID:', clean_doi, flags=re.IGNORECASE)[0]
        return (clean_doi, text.replace(full_match, '', 1))
    return ('', text)

def test(raw_text, fmt='ieee'):
    print(f"\nTesting: {raw_text}")
    print(f"Format: {fmt}")
    text = preprocess_ref(raw_text, fmt)
    doi, _ = extract_doi(text)
    print(f"Extracted DOI: '{doi}'")

# Original failing case
test("Q. Guo, X. Xie, Y. Li, X. Zhang, Y. Liu, X. Li, and C. Shen, “Audee: automated testing for deep learning frameworks,” in Proceedings of the 35th IEEE/ACM International Conference on Automated Software Engineering, ser. ASE ’20. New York, NY, USA: Association for Computing Machinery, 2021, p. 486–498. [Online]. Available: https://doi.org/10.1145/3324884.3416571", fmt='plos')

# Trailing bracket case
test("Ref (doi: 10.1001/jama.2016.0123)")

# dx.doi.org case
test("See https://dx.doi.org/10.1001/jama.2016.0123 for details")

# Common subdomain case
test("Link: https://www.doi.org/10.1145/3324884.3416571")
