import json
import re
import requests
from urllib.parse import quote
from difflib import SequenceMatcher

def check_or_find_doi(ref: dict) -> tuple[str, str]:
    doi = ref.get('doi', '')
    headers = {'User-Agent': 'DOIChecker/1.0 (mailto:jakiduy1410@gmail.com)'}
    if doi:
        clean_doi = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', doi, flags=re.IGNORECASE).strip()
        url = f'https://api.crossref.org/works/{quote(clean_doi)}'
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return ('valid_doi', clean_doi)
            elif resp.status_code == 404:
                return ('invalid_doi', clean_doi)
            else:
                return ('unverified', clean_doi)
        except requests.RequestException:
            return ('unverified', clean_doi)
    if ref.get('is_web', False):
        return ('web_resource', '')
    authors = ref.get('authors', '')
    ref_year = ref.get('year', '')
    if authors == '' and ref_year == '':
        return ('web_resource', '')
    title = ref.get('title', '')
    raw_text = ref.get('raw', '')
    search_query = ''
    if title and title != 'Không tách được':
        search_query = f'query.title={quote(title)}'
    elif raw_text:
        search_query = f'query.bibliographic={quote(raw_text)}'
    else:
        return ('no_doi', '')
    search_url = f'https://api.crossref.org/works?{search_query}&rows=5'
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            items = resp.json().get('message', {}).get('items', [])
            for item in items:
                try:
                    item_year = str(item.get('issued', {}).get('date-parts', [[None]])[0][0])
                except (IndexError, TypeError, AttributeError):
                    item_year = ''
                
                if title:
                    api_titles = item.get('title', [])
                    api_title = api_titles[0] if api_titles else ''
                    
                    score = SequenceMatcher(None, title.lower(), api_title.lower()).ratio()
                    if score < 0.85:
                        continue

                if not ref_year or ref_year == item_year:
                    return ('found_doi', item.get('DOI', ''))
        return ('no_doi', '')
    except requests.RequestException:
        return ('unverified', '')

def process_validation(job_id: str, filename: str, refs_data: list) -> dict:
    summary = {'total_refs': len(refs_data), 'original_has_doi': 0, 'valid_doi': 0, 'invalid_doi': 0, 'found_doi': 0, 'unverified': 0, 'no_doi': 0, 'web_resource': 0}
    final_references = []
    for index, ref in enumerate(refs_data, 1):
        status, final_doi = check_or_find_doi(ref)
        if ref.get('doi'):
            summary['original_has_doi'] += 1
        summary[status] += 1
        ref_with_status = {'index': index, **ref, 'doi': final_doi, 'doi_status': status}
        final_references.append(ref_with_status)
    return {'job_id': job_id, 'filename': filename, 'status': 'done', 'summary': summary, 'references': final_references}

