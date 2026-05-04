import re
from core.pdf_preprocessing import clean_parts

def detect_format(ref_data: str) -> str:
    """
    Dùng chung cho cả .docx và .txt
    """
    if re.search(r'^\s*(?:\*\*)?1\.(?:\*\*)?\s+', ref_data, re.MULTILINE):
        return 'plos'
    if re.search(r'^\s*(?:-\s*|\*\*\s*)*\\?\[1\\?\]', ref_data, re.MULTILINE):
        return 'ieee'
    
    if len(re.findall(r'^\s*(?:\*\*)?\d+\.(?:\*\*)?\s+', ref_data, re.MULTILINE)) > 2:
        return 'plos'
    if len(re.findall(r'^\s*(?:-\s*|\*\*\s*)*\\?\[\d+\\?\]', ref_data, re.MULTILINE)) > 2:
        return 'ieee'

    if re.search(r'^\s*-\s+[A-Z]', ref_data, re.MULTILINE):
        return 'dash_newline'
    if ' - ' in ref_data and len(ref_data.split('\n')) < 5:
        return 'apa_inline'
    return 'author_year'

def get_docx_references(md_content: str, source_name: str = "Tài liệu") -> tuple[list[str], str]:
    # 0. Strip images (base64 noise)
    md_content = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)

    # 1. Trích xuất phần References
    # Tìm các heading phổ biến: References, Bibliography, Tài liệu tham khảo
    ref_pattern = r'(?im)^[\#\*\_\s]*\**\_*(?:References?|Bibliography|Tài liệu tham khảo|REFERENCES)\_*\**[\:\*\_\s]*$'
    ref_location = re.search(ref_pattern, md_content)
    
    found_heading = False
    if not ref_location:
        print(f'[!] Khong tim thay muc References trong: {source_name}. Dang fallback lay toan bo noi dung.')
        ref_data = md_content
    else:
        ref_data = md_content[ref_location.end():]
        found_heading = True
    
    if found_heading:
        # Chỉ thực hiện cắt phụ lục nếu chúng ta đã tìm thấy Heading References
        # (Tránh việc cắt nhầm ngay từ Introduction nếu fallback lấy cả bài)
        
        # Xóa phụ lục ở cuối file (các thẻ heading # lớn hoặc các section bold như Acknowledgements, Appendix)
        # Dừng lại nếu gặp một heading mới hoặc một dòng Bold lớn (thường là tiêu đề section tiếp theo)
        ref_data = re.split(r'(?m)^(?:\#+\s+.+|\*\*[A-Z][^\n\.]{2,80}\*\*)\s*$', ref_data, maxsplit=1)[0]
        
        # Cắt bỏ các metadata thừa thãi thường gặp sau danh sách (như Affiliation, Journal info)
        # Nếu thấy dòng bắt đầu bằng "Figure" hoặc "Table" đơn lẻ, cũng có thể là bắt đầu phần Appendix
        ref_data = re.split(r'(?m)^\s*(?:Figure|Table|Appendix|Phụ lục)\s+\d+', ref_data, maxsplit=1)[0]
    
    # 2. Clean Markdown formatting
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', ref_data)
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = text.replace('\\', '')
    
    # Merge hyphenated line breaks before line splitting
    text = re.sub(r'-\n\s*', '', text)

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
        
        # Strict Start Detection
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
                # Thêm Regex nhận diện dòng bắt đầu bằng URL/DOI để tự động nối vào ref trước
                if re.match(r'^\s*(?:https?://|doi:|www\.)', stripped):
                    is_start = False
                # Bổ sung regex nhận diện dòng có Tên tác giả + (Năm)
                # để tách ref mới ngay cả khi chúng dính lẹo vào nhau (blank_lines == 0)
                elif blank_lines > 0 or re.match(r'^[A-Z][^\n\d(]+?\(\d{4}[a-z]?\)', stripped):
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
                    
        # Merge or Append Policy
        if is_start:
            healed_lines.append(stripped)
        else:
            healed_lines[-1] += " " + stripped
            
        blank_lines = 0

    if fmt == 'apa_inline':
        ref_data_joined = " ".join(healed_lines)
        healed_lines = re.split(r'\s+-\s+(?=[A-Z][a-z])', ref_data_joined)
            
    # Tái sử dụng logic làm sạch dữ liệu
    clean_parts_list = clean_parts(healed_lines)
            
    # Thêm .encode('ascii', 'ignore').decode() để tránh lỗi encoding khi in ra console Windows
    print(f'[{source_name.encode("ascii", "ignore").decode()}] format={fmt}  refs={len(clean_parts_list)}')
    
    return (clean_parts_list, fmt)