import os
import json
from bs4 import BeautifulSoup

def extract_metadata():
    input_dir = "backend/testing/tmp_result"
    output_dir = "backend/testing/json_result"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith(".xml"):
            xml_path = os.path.join(input_dir, filename)
            print(f"Extracting from {filename}...")

            with open(xml_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'xml')

            references = []
            
            # Grobid TEI XML uses biblStruct for citations
            bibl_structs = soup.find_all('biblStruct')
            
            for i, bibl in enumerate(bibl_structs, 1):
                ref_data = {
                    "index": i,
                    "authors": "",
                    "year": "",
                    "title": "",
                    "journal": "",
                    "doi": "",
                    "raw": ""
                }
                
                # Title
                title_tag = bibl.find('title', level='a') or bibl.find('title')
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
                    if pub_title:
                        ref_data['journal'] = pub_title.get_text(strip=True)
                    
                    imprint = monogr.find('imprint')
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
                
                # Raw Citation (as requested)
                raw_tag = bibl.find('note', type='raw_reference')
                if raw_tag:
                    ref_data['raw'] = raw_tag.get_text(strip=True)
                
                references.append(ref_data)
            
            output_filename = filename.replace(".xml", ".json")
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as out_f:
                json.dump(references, out_f, indent=4, ensure_ascii=False)
            
            print(f"Extracted {len(references)} references to {output_path}")

if __name__ == "__main__":
    extract_metadata()
