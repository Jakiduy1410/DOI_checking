import os
import json
import uuid
from pathlib import Path
from dataclasses import asdict

from core.preprocessing import get_references
from core.masking import masking
from core.doi_validator import process_validation
from core.document_converter import convert_to_md

def pipeline():
    base_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    temp_dir = base_dir / 'temporary'
    result_dir = base_dir / 'result'


    print(f"Quét thư mục tạm: {temp_dir}")
    
    target_files = [f for f in temp_dir.glob("*.*") if f.suffix.lower() in ['.pdf', '.txt', '.docx', '.doc']]
    
    if not target_files:
        print("Không tìm thấy tệp tài liệu nào cần xử lý trong thư mục temporary/.\n")
        return

    target_files.sort(key=lambda x: x.stat().st_mtime)

    print(f"Tìm thấy {len(target_files)} tệp tài liệu. Bắt đầu xử lý...\n")

    for doc_file in target_files:
        print(f"{'='*60}")
        print(f"Đang xử lý: {doc_file.name}")
        
        try:
            
            md_content = convert_to_md(str(doc_file))
            
            
            refs_str, fmt = get_references(md_content, source_name=doc_file.name)
            
            if not refs_str:
                print("Không tìm thấy reference nào trong file này.")
                refs_data = []
            else:
                refs_structured = masking(refs_str, fmt)
                refs_data = [asdict(ref) for ref in refs_structured]
                print(f"Đã trích xuất thành công {len(refs_data)} references.")
            
            job_id = f"job_local_{uuid.uuid4().hex[:8]}"
            validation_result = process_validation(
                job_id=job_id, 
                filename=doc_file.name, 
                refs_data=refs_data
            )
            
            summary = validation_result.get('summary', {})
            print(f"Kết quả: Valid: {summary.get('valid_doi', 0)} | Found: {summary.get('found_doi', 0)} | Invalid: {summary.get('invalid_doi', 0)}")

            json_filename = doc_file.name + ".json"
            json_path = result_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(validation_result, f, ensure_ascii=False, indent=4)
            print(f"Đã lưu JSON thành công tại: result/{json_filename}")
            
            #Khi nào delpoy hoàn chỉnh sẽ uncomment cái này để xóa file đi
            # doc_file.unlink()
            # print(f"Đã dọn dẹp file tham chiếu gốc temporary/{doc_file.name}")

        except Exception as e:
            print(f"[LỖI] Dừng đột ngột ở file {doc_file.name}. Chi tiết: {e}")

    print(f"\n{'='*60}")
    print("LUỒNG KIỂM THỬ ĐÃ CHẠY XONG!")

# if __name__ == '__main__':
#     main()
