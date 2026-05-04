import os
import json
import uuid
from pathlib import Path
from dataclasses import asdict

from core.pdf_preprocessing import get_references
from core.docx_preprocessing import get_docx_references
from core.masking import masking
from core.doi_validator import process_validation
from core.document_converter import convert_to_md, convert_docx_to_pdf
from core.grobid_parser import process_pdf_with_grobid

def pipeline(session_id: str = None):
    base_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    temp_dir = base_dir / 'temporary'
    result_dir = base_dir / 'result'
    
    if session_id:
        temp_dir = temp_dir / session_id
        result_dir = result_dir / session_id
        
    result_dir.mkdir(parents=True, exist_ok=True)

    print(f"Quet thu muc: {temp_dir}")
    
    if not temp_dir.exists():
        print(f"Thu muc {temp_dir} khong ton tai.")
        return

    target_files = [f for f in temp_dir.glob("*.*") if f.suffix.lower() in ['.pdf', '.txt', '.docx', '.doc']]
    
    if not target_files:
        print("Khong tim thay tep tai lieu nao can xu ly trong thu muc temporary/.\n")
        return

    target_files.sort(key=lambda x: x.stat().st_mtime)

    for doc_file in target_files:
        print(f"{'='*60}")
        print(f"Dang xu ly: {doc_file.name}")
        
        try:
            if doc_file.suffix.lower() == '.doc':
                print(f"[LOI] File {doc_file.name} khong dung dinh dang vui long doi file thanh docx hoac pdf")
                doc_file.unlink()
                continue
                
            if doc_file.suffix.lower() == '.pdf':
                try:
                    print(f"-> Dang gui {doc_file.name} cho Grobid API xu ly...")
                    refs_data = process_pdf_with_grobid(str(doc_file))
                    if not refs_data:
                        print("Không tìm thấy reference nào trong file này (Grobid).")
                    else:
                        print(f"Da trich xuat thanh cong {len(refs_data)} references bang Grobid.")
                except Exception as ex:
                    print(f"[CẢNH BÁO] Grobid xu ly that bai: {ex}. Chuyen sang luong du phong (Markdown).")
                    md_content = convert_to_md(str(doc_file))
                    refs_str, fmt = get_references(md_content, source_name=doc_file.name)
                    if not refs_str:
                        print("Khong tim thay reference nao trong file nay (Fallback).")
                        refs_data = []
                    else:
                        refs_structured = masking(refs_str, fmt)
                        refs_data = [asdict(ref) for ref in refs_structured]
                        print(f"Da trich xuat thanh cong {len(refs_data)} references bang Fallback.")
            elif doc_file.suffix.lower() == '.docx':
                # --- LUỒNG CHÍNH: Chuyển sang PDF để dùng Grobid ---
                temp_pdf_path = doc_file.with_suffix('.pdf')
                grobid_success = False
                
                try:
                    print(f"-> Dang thu nghiem chuyen doi {doc_file.name} sang PDF de dung Grobid...")
                    if convert_docx_to_pdf(str(doc_file), str(temp_pdf_path)):
                        print(f"-> Chuyen doi thanh cong. Dang gui cho Grobid...")
                        refs_data = process_pdf_with_grobid(str(temp_pdf_path))
                        if refs_data:
                            print(f"Da trich xuat thanh cong {len(refs_data)} references tu DOCX (qua Grobid).")
                            grobid_success = True
                        else:
                            print("Grobid khong tim thay references trong file DOCX da chuyen doi.")
                    else:
                        print("Khong the chuyen doi DOCX sang PDF.")
                except Exception as g_ex:
                    print(f"[CANH BAO] Luong Grobid cho DOCX gap loi: {g_ex}")
                finally:
                    # Xóa file PDF tạm nếu có
                    if temp_pdf_path.exists():
                        temp_pdf_path.unlink()

                # --- LUỒNG DỰ PHÒNG (Code cũ): Nếu Grobid thất bại hoặc không có dữ liệu ---
                if not grobid_success:
                    print(f"-> Chuyen sang luong du phong (MarkItDown) cho {doc_file.name}...")
                    md_content = convert_to_md(str(doc_file))
                    refs_str, fmt = get_docx_references(md_content, source_name=doc_file.name)
                    if not refs_str:
                        print("Khong tim thay reference nao trong file nay (Fallback).")
                        refs_data = []
                    else:
                        refs_structured = masking(refs_str, fmt)
                        refs_data = [asdict(ref) for ref in refs_structured]
                        print(f"Da trich xuat thanh cong {len(refs_data)} references bang Fallback.")
            elif doc_file.suffix.lower() == '.txt':
                print(f"-> Dang xu ly file van ban: {doc_file.name}")
                md_content = convert_to_md(str(doc_file))
                # Su dung chung logic preprocessing voi docx vi cung la dang text/markdown
                refs_str, fmt = get_docx_references(md_content, source_name=doc_file.name)
                if not refs_str:
                    print("Khong tim thay reference nao trong file nay.")
                    refs_data = []
                else:
                    refs_structured = masking(refs_str, fmt)
                    refs_data = [asdict(ref) for ref in refs_structured]
                    print(f"Da trich xuat thanh cong {len(refs_data)} references.")
            else:
                print(f"[LỖI] File {doc_file.name} không được hỗ trợ.")
                doc_file.unlink()
                continue
            
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
            
            # Don dep file sau khi xu ly thanh cong
            doc_file.unlink()
            print(f"Da don dep file tham chieu goc: {doc_file.name}")

        except Exception as e:
            print(f"[LOI] Dung dot ngot o file {doc_file.name}. Chi tiet: {e}")
            if doc_file.exists():
                doc_file.unlink()
                print(f"Da don dep file loi: {doc_file.name}")

    # Dọn dẹp thư mục session nếu rỗng
    if session_id and temp_dir.exists() and not any(temp_dir.iterdir()):
        try:
            temp_dir.rmdir()
            print(f"Da don dep thu muc session: {session_id}")
        except Exception as e:
            print(f"Khong the xoa thu muc session {session_id}: {e}")

    print(f"\n{'='*60}")
    print("Hoan tat quy trinh xu ly.")

if __name__ == '__main__':
    pipeline()
