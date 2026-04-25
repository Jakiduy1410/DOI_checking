import os
import json
import uuid
from pathlib import Path
from dataclasses import asdict

from core.pdf_preprocessing import get_references
from core.docx_preprocessing import get_docx_references
from core.masking import masking
from core.doi_validator import process_validation
from core.document_converter import convert_to_md

def pipeline():
    base_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    temp_dir = base_dir / 'temporary'
    result_dir = base_dir / 'result'


    print(f"Quet thu muc tam: {temp_dir}")
    
    target_files = [f for f in temp_dir.glob("*.*") if f.suffix.lower() in ['.pdf', '.txt', '.docx', '.doc']]
    
    if not target_files:
        print("Không tìm thấy tệp tài liệu nào cần xử lý trong thư mục temporary/.\n")
        return

    target_files.sort(key=lambda x: x.stat().st_mtime)

    for doc_file in target_files:
        print(f"{'='*60}")
        print(f"Dang xu ly: {doc_file.name}")
        
        try:
            if doc_file.suffix.lower() == '.doc':
                print(f"[LỖI] File {doc_file.name} không đúng định dạng vui lòng đổi file thành docx hoặc pdf")
                continue
                
            md_content = convert_to_md(str(doc_file))
            
            if doc_file.suffix.lower() == '.pdf':
                refs_str, fmt = get_references(md_content, source_name=doc_file.name)
            elif doc_file.suffix.lower() == '.docx':
                refs_str, fmt = get_docx_references(md_content, source_name=doc_file.name)
            else:
                print(f"[LỖI] File {doc_file.name} không được hỗ trợ.")
                continue
            
            if not refs_str:
                print("Không tìm thấy reference nào trong file này.")
                refs_data = []
            else:
                refs_structured = masking(refs_str, fmt)
                refs_data = [asdict(ref) for ref in refs_structured]
                print(f"Da trich xuat thanh cong {len(refs_data)} references.")
            
            job_id = f"job_local_{uuid.uuid4().hex[:8]}"
            validation_result = process_validation(
                job_id=job_id, 
                filename=doc_file.name, 
                refs_data=refs_data
            )
            
            summary = validation_result.get('summary', {})
            print(f"Ket qua: Valid: {summary.get('valid_doi', 0)} | Found: {summary.get('found_doi', 0)} | Invalid: {summary.get('invalid_doi', 0)}")

            file_ext = doc_file.suffix[1:].lower()
            json_filename = f"{doc_file.stem}_{file_ext}.json"
            json_path = result_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(validation_result, f, ensure_ascii=False, indent=4)
            print(f"Da luu JSON thanh cong tai: result/{json_filename}")
            
            #Khi nào delpoy hoàn chỉnh sẽ uncomment cái này để xóa file đi
            # doc_file.unlink()
            # print(f"Đã dọn dẹp file tham chiếu gốc temporary/{doc_file.name}")

        except Exception as e:
            print(f"[LOI] Dung dot ngot o file {doc_file.name}. Chi tiet: {e}")

    print(f"\n{'='*60}")
    print("LUONG KIEM THU DA CHAY XONG!")

if __name__ == '__main__':
    pipeline()
