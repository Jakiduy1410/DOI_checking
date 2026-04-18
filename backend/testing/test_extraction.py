import os
import glob
import re
from markitdown import MarkItDown

def extract_references(md_text):
    """
    Extracts the References section from a markdown string and truncates
    any trailing tables, images, or appendices.
    """
    # 1. Locate the References section
    # Matches: References, Bibliography, Works Cited (optionally with markdown headers or bold/italic)
    ref_pattern = re.compile(r"(?im)^(?:#+\s*)?(?:\*\*|__)?(?:References|Bibliography|Works Cited)(?:\*\*|__)?[\s]*$")
    
    # Find all matches in case there are multiple (e.g., in a compilation). Wait, usually we look for the last one
    # or just the standard one at the end. We'll find the last occurrence to be safe.
    matches = list(ref_pattern.finditer(md_text))
    
    if not matches:
        return "NO REFERENCES FOUND"
    
    # We take the text after the last match
    last_match = matches[-1]
    
    # SỬA Ở ĐÂY: Thay last_match.end() thành last_match.start()
    # Phải lấy từ start() để giữ lại cái chữ "References". Nếu cắt bằng end(), 
    # file test.py tóm được md_text sẽ báo lỗi "Không tìm thấy mục References" ngay!
    ref_section = md_text[last_match.end():] 
    
    # 2. Truncate trailing content
    # We want to find the FIRST occurrence of any of these elements in the ref_section
    truncation_patterns = [
        r"(?im)^(?:#+\s*)?(?:\*\*|__)?(?:Appendices|Appendix)", # Appendices
        r"!\[.*?\]\(.*?\)", # Markdown Image
        r"\|.*?\|" # Row in a Markdown table
    ]
    
    earliest_truncation_index = len(ref_section)
    
    for pattern in truncation_patterns:
        match = re.search(pattern, ref_section)
        if match:
            # If we find a truncation marker earlier than our current cutoff, update it
            if match.start() < earliest_truncation_index:
                earliest_truncation_index = match.start()
                
    # Truncate the text
    clean_refs = ref_section[:earliest_truncation_index].strip()
    return clean_refs

def process_all_docx(frontend_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    docx_files = glob.glob(os.path.join(frontend_dir, "*.docx"))
    
    md_converter = MarkItDown()
    
    for docx_path in docx_files:
        filename = os.path.basename(docx_path)
        output_filename = filename.replace('.docx', '.md')
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Processing: {filename}...")
        try:
            # Convert
            result = md_converter.convert(docx_path)
            raw_md = result.text_content
            
            # Extract references
            extracted_refs = extract_references(raw_md)
            
            # Save to output folder
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_refs)
            print(f"  -> Saved extracted references to {output_filename}")
            
        except Exception as e:
            print(f"  -> Error processing {filename}: {e}")

if __name__ == "__main__":
    FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "extracted_references")
    
    process_all_docx(FRONTEND_DIR, OUTPUT_DIR)
