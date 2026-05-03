import requests
import urllib.parse
from bs4 import BeautifulSoup
from core.masking import is_website, ACADEMIC_DOMAINS

GROBID_URL = "http://localhost:8070/api/processReferences"

def process_pdf_with_grobid(pdf_path: str) -> list[dict]:
    """
    Gửi PDF tới Grobid để trích xuất references.
    Trộn kết quả trả về thành list các dictionary chứa thông tin:
    index, authors, year, title, journal, doi, raw, is_web
    """
    # Gửi request tới Grobid
    with open(pdf_path, 'rb') as f:
        files = {'input': f}
        data = {
            'consolidateCitations': '0',
            'includeRawCitations': '1'
        }
        
        response = requests.post(GROBID_URL, files=files, data=data, timeout=120)
        response.raise_for_status()  # Nếu lỗi HTTP sẽ throw exception

    # Phân tích XML
    soup = BeautifulSoup(response.text, 'xml')
    references = []
    
    bibl_structs = soup.find_all('biblStruct')
    for i, bibl in enumerate(bibl_structs, 1):
        ref_data = {
            "index": i,
            "authors": "",
            "year": "",
            "title": "",
            "journal": "",
            "doi": "",
            "raw": "",
            "is_web": False
        }
        
        # Title
        title_tag = bibl.find('title', level='a')
        is_analytic = True
        if not title_tag:
            title_tag = bibl.find('title')
            is_analytic = False
            
        if title_tag:
            ref_data['title'] = title_tag.get_text(strip=True)
            
        # Authors
        authors = []
        for author in bibl.find_all('author'):
            pers_name = author.find('persName')
            if pers_name:
                first_name = pers_name.find('forename', type='first')
                last_name = pers_name.find('surname')
                
                name_parts = []
                if first_name:
                    name_parts.append(first_name.get_text(strip=True))
                if last_name:
                    name_parts.append(last_name.get_text(strip=True))
                
                if name_parts:
                    authors.append(" ".join(name_parts))
        
        if authors:
            ref_data['authors'] = ", ".join(authors)
        
        # Journal / Publication
        monogr = bibl.find('monogr')
        if monogr:
            pub_title = monogr.find('title')
            imprint = monogr.find('imprint')
            publisher = imprint.find('publisher') if imprint else monogr.find('publisher')
            
            if is_analytic and pub_title:
                ref_data['journal'] = pub_title.get_text(strip=True)
            elif publisher:
                ref_data['journal'] = publisher.get_text(strip=True)
            elif pub_title:
                ref_data['journal'] = pub_title.get_text(strip=True)
            
            if imprint:
                date_tag = imprint.find('date')
                if date_tag and date_tag.has_attr('when'):
                    ref_data['year'] = date_tag['when']
                elif date_tag:
                    ref_data['year'] = date_tag.get_text(strip=True)
        
        # DOI
        doi_tag = bibl.find('idno', type='DOI')
        if doi_tag:
            ref_data['doi'] = doi_tag.get_text(strip=True)
        
        # Raw Citation
        raw_tag = bibl.find('note', type='raw_reference')
        if raw_tag:
            ref_data['raw'] = raw_tag.get_text(strip=True)

        # Check is_web
        if ref_data['doi']:
            ref_data['is_web'] = False
        else:
            ptr_tag = bibl.find('ptr', target=True)
            if ptr_tag:
                url = ptr_tag['target']
                try:
                    domain = urllib.parse.urlparse(url).netloc.lower()
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    is_academic = any(domain == d or domain.endswith('.' + d) for d in ACADEMIC_DOMAINS)
                    ref_data['is_web'] = not is_academic
                except Exception:
                    ref_data['is_web'] = True
            else:
                ref_data['is_web'] = False

        references.append(ref_data)
        
    return references
