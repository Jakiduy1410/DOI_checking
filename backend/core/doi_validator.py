# doi_validator.py
from __future__ import annotations

import os
import re
import threading
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_thread_local = threading.local()


def _get_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))
        _thread_local.session = session
    return session


def _clean_doi(doi: str) -> str:
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", doi, flags=re.IGNORECASE).strip()


def check_or_find_doi(ref: dict) -> tuple[str, str]:
    doi = ref.get("doi", "")
    contact_email = os.getenv("CROSSREF_EMAIL", "jakiduy1410@gmail.com")
    headers = {"User-Agent": f"DOIChecker/1.0 (mailto:{contact_email})"}
    session = _get_session()

    if doi:
        clean_doi = _clean_doi(doi)
        url = f"https://api.crossref.org/works/{quote(clean_doi)}"
        try:
            resp = session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return ("valid_doi", clean_doi)
            if resp.status_code == 404:
                return ("invalid_doi", clean_doi)
            return ("unverified", clean_doi)
        except requests.RequestException:
            return ("unverified", clean_doi)

    if ref.get("is_web", False):
        return ("web_resource", "")

    authors = ref.get("authors", "")
    ref_year = ref.get("year", "")
    if not authors and not ref_year:
        return ("web_resource", "")

    title = ref.get("title", "")
    raw_text = ref.get("raw", "")

    if title and title != "Không tách được":
        search_query = f"query.title={quote(title)}"
    elif raw_text:
        search_query = f"query.bibliographic={quote(raw_text)}"
    else:
        return ("no_doi", "")

    search_url = f"https://api.crossref.org/works?{search_query}&rows=5"
    try:
        resp = session.get(search_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            items = resp.json().get("message", {}).get("items", [])
            for item in items:
                try:
                    item_year = str(item.get("issued", {}).get("date-parts", [[None]])[0][0])
                except (IndexError, TypeError, AttributeError):
                    item_year = ""

                if title:
                    api_titles = item.get("title", [])
                    api_title = api_titles[0] if api_titles else ""
                    if SequenceMatcher(None, title.lower(), api_title.lower()).ratio() < 0.85:
                        continue

                if not ref_year or ref_year == item_year:
                    return ("found_doi", item.get("DOI", ""))
        return ("no_doi", "")
    except requests.RequestException:
        return ("unverified", "")


def process_validation(job_id: str, filename: str, refs_data: list) -> dict:
    summary = {
        "total_refs": len(refs_data),
        "original_has_doi": 0,
        "valid_doi": 0,
        "invalid_doi": 0,
        "found_doi": 0,
        "unverified": 0,
        "no_doi": 0,
        "web_resource": 0,
    }

    final_references = [None] * len(refs_data)

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_index = {
            executor.submit(check_or_find_doi, ref): (i, ref)
            for i, ref in enumerate(refs_data)
        }

        for future in as_completed(future_to_index):
            i, ref = future_to_index[future]
            try:
                status, final_doi = future.result()
            except Exception as e:
                print(f"[!] Lỗi kết nối ở tham khảo số {i + 1}: {e}")
                status, final_doi = "unverified", ""

            if ref.get("doi"):
                summary["original_has_doi"] += 1
            summary[status] = summary.get(status, 0) + 1

            final_references[i] = {"index": i + 1, **ref, "doi": final_doi, "doi_status": status}

    return {
        "job_id": job_id,
        "filename": filename,
        "status": "done",
        "summary": summary,
        "references": final_references,
    }