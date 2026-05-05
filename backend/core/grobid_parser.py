# grobid_parser.py
from __future__ import annotations

import urllib.parse

import requests
from bs4 import BeautifulSoup

from core.masking import ACADEMIC_DOMAINS

GROBID_URL = "http://localhost:8070/api/processReferences"


def _normalize_domain(url: str) -> str:
    domain = urllib.parse.urlparse(url).netloc.lower()
    return domain[4:] if domain.startswith("www.") else domain


def _is_academic_target(url: str) -> bool:
    domain = _normalize_domain(url)
    return any(domain == d or domain.endswith("." + d) for d in ACADEMIC_DOMAINS)


def process_pdf_with_grobid(pdf_path: str) -> list[dict]:
    with open(pdf_path, "rb") as f:
        response = requests.post(
            GROBID_URL,
            files={"input": f},
            data={"consolidateCitations": "0", "includeRawCitations": "1"},
            timeout=120,
        )
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "xml")
    references: list[dict] = []

    for i, bibl in enumerate(soup.find_all("biblStruct"), 1):
        ref_data = {
            "index": i,
            "authors": "",
            "year": "",
            "title": "",
            "journal": "",
            "doi": "",
            "raw": "",
            "is_web": False,
        }

        title_tag = bibl.find("title", level="a")
        if title_tag is None:
            title_tag = bibl.find("title")

        if title_tag is not None:
            ref_data["title"] = title_tag.get_text(strip=True)

        authors = []
        for author in bibl.find_all("author"):
            pers_name = author.find("persName")
            if not pers_name:
                continue

            first_name = pers_name.find("forename", type="first")
            last_name = pers_name.find("surname")
            name_parts = []
            if first_name:
                name_parts.append(first_name.get_text(strip=True))
            if last_name:
                name_parts.append(last_name.get_text(strip=True))
            if name_parts:
                authors.append(" ".join(name_parts))

        if authors:
            ref_data["authors"] = ", ".join(authors)

        monogr = bibl.find("monogr")
        if monogr:
            pub_title = monogr.find("title")
            imprint = monogr.find("imprint")
            publisher = imprint.find("publisher") if imprint else monogr.find("publisher")

            if bibl.find("title", level="a") and pub_title:
                ref_data["journal"] = pub_title.get_text(strip=True)
            elif publisher:
                ref_data["journal"] = publisher.get_text(strip=True)
            elif pub_title:
                ref_data["journal"] = pub_title.get_text(strip=True)

            if imprint:
                date_tag = imprint.find("date")
                if date_tag and date_tag.has_attr("when"):
                    ref_data["year"] = date_tag["when"]
                elif date_tag:
                    ref_data["year"] = date_tag.get_text(strip=True)

        doi_tag = bibl.find("idno", type="DOI")
        if doi_tag:
            ref_data["doi"] = doi_tag.get_text(strip=True)

        raw_tag = bibl.find("note", type="raw_reference")
        if raw_tag:
            ref_data["raw"] = raw_tag.get_text(strip=True)

        if ref_data["doi"]:
            ref_data["is_web"] = False
        else:
            ptr_tag = bibl.find("ptr", target=True)
            if ptr_tag:
                try:
                    ref_data["is_web"] = not _is_academic_target(ptr_tag["target"])
                except Exception:
                    ref_data["is_web"] = True
            else:
                ref_data["is_web"] = False

        references.append(ref_data)

    return references