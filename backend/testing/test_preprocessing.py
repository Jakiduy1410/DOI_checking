import os
import glob
import re
import json
# SỬA Ở ĐÂY: Bỏ import detect_format từ test.py, tự viết lại hàm xịn hơn ở dưới để chống lừa
from test import clean_parts

def detect_format(ref_data: str) -> str:
    """
    SỬA Ở ĐÂY: Phiên bản nâng cấp miễn nhiễm với lỗi rớt trang DOCX (như số "949.")
    """
    # Chắc chắn là plos/ieee nếu bắt đầu bằng đúng "1." hoặc "[1]"
    if re.search(r'^\s*(?:\*\*)?1\.(?:\*\*)?\s+', ref_data, re.MULTILINE):
        return 'plos'
    if re.search(r'^\s*(?:-\s*|\*\*\s*)*\\?\[1\\?\]', ref_data, re.MULTILINE):
        return 'ieee'
    
    # Đếm thử xem có >2 dòng bắt đầu bằng số không (tránh bị lừa bởi 1 dòng rớt số trang duy nhất)
    if len(re.findall(r'^\s*(?:\*\*)?\d+\.(?:\*\*)?\s+', ref_data, re.MULTILINE)) > 2:
        return 'plos'
    if len(re.findall(r'^\s*(?:-\s*|\*\*\s*)*\\?\[\d+\\?\]', ref_data, re.MULTILINE)) > 2:
        return 'ieee'

    if re.search(r'^\s*-\s+[A-Z]', ref_data, re.MULTILINE):
        return 'dash_newline'
    if ' - ' in ref_data and len(ref_data.split('\n')) < 5:
        return 'apa_inline'
    return 'author_year'

def format_references(raw_md):
    # 1. Clean Markdown formatting
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', raw_md)
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = text.replace('\\', '')
    
    # Merge hyphenated line breaks before line splitting
    text = re.sub(r'-\n\s*', '', text)

    # Đã tự dùng detect_format cục bộ xịn hơn ở trên
    fmt = detect_format(text)
    
    lines = text.split('\n')
    
    healed_lines = []
    blank_lines = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1 
            continue
            
        is_start = False
        
        # 2. Strict Start Detection
        if not healed_lines:
            is_start = True
        else:
            prev_ref = healed_lines[-1]
            if fmt == 'plos' and re.match(r'^\s*\d+\.\s+', stripped):
                is_start = True
            elif fmt == 'ieee' and re.match(r'^\s*(?:-\s*)?\[\d+\]', stripped):
                is_start = True
            elif fmt == 'dash_newline' and re.match(r'^\s*-\s+[A-Z]', stripped):
                is_start = True
            elif fmt == 'author_year':
                if blank_lines > 0:
                    # SỬA Ở ĐÂY: Thêm '–' (en-dash) vào prev_ref và thêm \d+ vào stripped để gom cổ mấy số trang rớt dòng dính lại với dòng trên
                    if prev_ref.endswith((',', ' and', ' &', '-', '–', 'et al.')):
                        is_start = False
                    elif re.match(r'^([a-z]|\(|http|doi|www|\d+)', stripped): 
                        is_start = False
                    else:
                        is_start = True 
                else:
                    is_start = False
            elif fmt == 'apa_inline':
                is_start = False 
                    
        # 3. Merge or Append Policy
        if is_start:
            healed_lines.append(stripped)
        else:
            healed_lines[-1] += " " + stripped
            
        blank_lines = 0

    # Fallback for apa_inline format
    if fmt == 'apa_inline':
        ref_data_joined = " ".join(healed_lines)
        healed_lines = re.split(r'\s+-\s+(?=[A-Z][a-z])', ref_data_joined)
            
    # Tái sử dụng vũ khí dọn rác clean_parts của test.py
    clean_parts_list = clean_parts(healed_lines)
            
    # Final pass: normalize spaces and index
    final_refs = []
    
    for i, r in enumerate(clean_parts_list, start=1):
        if r:
            final_refs.append({
                "index": i,
                "reference": r
            })
        
    return final_refs

def process_extracted_files(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    md_files = glob.glob(os.path.join(input_dir, "*.md"))
    
    for md_path in md_files:
        filename = os.path.basename(md_path)
        print(f"Formatting {filename}...")
        
        with open(md_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        formatted_list= format_references(raw_content)
        
        # Save as JSON to see the exact resulting array
        json_filename = filename.replace('.md', '.json')
        output_path = os.path.join(output_dir, json_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_list, f, indent=4, ensure_ascii=False)
            
        print(f"  -> Extracted {len(formatted_list)} references to {json_filename}")

if __name__ == "__main__":
    INPUT_DIR = os.path.join(os.path.dirname(__file__), "extracted_references")
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "formatted_references")
    process_extracted_files(INPUT_DIR, OUTPUT_DIR)