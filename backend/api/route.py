from fastapi import APIRouter, UploadFile, File, Form
import os
import shutil
import json
import uuid
from pathlib import Path
from tasks import pipeline

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temporary"
RESULT_DIR = BASE_DIR / "result"

for d in [TEMP_DIR, RESULT_DIR]:
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] Đã tạo thư mục: {d}")
    else:
        print(f"[DEBUG] Thư mục đã tồn tại: {d}")

@router.post("/process")
async def process_upload(files: list[UploadFile] = File(...)):
    session_id = str(uuid.uuid4())[:8]
    session_dir = TEMP_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[DEBUG] Session {session_id}: Nhận được yêu cầu xử lý {len(files)} file.")
    
    for file in files:
        try:
            file_path = session_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"[DEBUG] Session {session_id}: Đã lưu file: {file.filename}")
        except Exception as e:
            print(f"[ERROR] Session {session_id}: Lỗi khi lưu file {file.filename}: {e}")

    print(f"[DEBUG] Session {session_id}: Bắt đầu chạy pipeline...")
    try:
        pipeline(session_id=session_id)
        print(f"[DEBUG] Session {session_id}: Pipeline đã hoàn thành.")
    except Exception as e:
        print(f"[ERROR] Session {session_id}: Pipeline gặp sự cố: {e}")
        return {"results": [{"filename": f.filename, "status": "error", "error": "Pipeline failure"} for f in files]}

    results = []
    for file in files:
        try:
            if file.filename.lower().endswith('.doc'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": "doc file sẽ trả kết quả là ko đúng định dạng vui lòng đổi file thành docx hoặc pdf",
                    "dois": [],
                    "totalFound": 0
                })
                continue
                
            path_obj = Path(file.filename)
            file_ext = path_obj.suffix[1:].lower()
            json_filename = f"{path_obj.stem}_{file_ext}.json"
            session_result_dir = RESULT_DIR / session_id
            json_path = session_result_dir / json_filename
            
            print(f"[DEBUG] Đang tìm kết quả: {json_path}")
            
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    raw_result = json.load(f)
                
                summary = raw_result.get("summary", {})
                mapped_result = {
                    "filename": raw_result.get("filename"),
                    "status": raw_result.get("status"),
                    "totalFound": summary.get("total_refs", 0),
                    "validCount": summary.get("valid_doi", 0) + summary.get("found_doi", 0),
                    "invalidCount": summary.get("invalid_doi", 0),
                    "textLength": 0,
                    "dois": []
                }
                
                for ref in raw_result.get("references", []):
                    status = ref.get("doi_status")
                    is_valid = status in ["valid_doi", "found_doi"]
                    
                    error_msg = None
                    if status == "invalid_doi":
                        error_msg = "DOI này không tồn tại hoặc không hợp lệ"
                    elif status == "no_doi":
                        error_msg = "Không tìm thấy DOI phù hợp trên Crossref"
                    elif status == "web_resource":
                        error_msg = "Tài nguyên Web (Bỏ qua kiểm tra DOI)"
                    elif status == "unverified":
                        error_msg = "Lỗi kết nối API (Chưa xác thực được)"

                    mapped_result["dois"].append({
                        "doi": ref.get("doi") or "No DOI",
                        "valid": is_valid,
                        "title": ref.get("title") or "Không rõ tiêu đề",
                        "authors": ref.get("authors") or "Không rõ tác giả",
                        "journal": ref.get("journal") or "N/A",
                        "year": ref.get("year") or "N/A",
                        "url": f"https://doi.org/{ref.get('doi')}" if ref.get("doi") else "#",
                        "type": "Article",
                        "error": error_msg
                    })

                results.append(mapped_result)
            else:
                print(f"[ERROR] Không tìm thấy JSON cho {file.filename} -> {json_path}")
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": f"Không tìm thấy file kết quả {json_filename}.",
                    "dois": [],
                    "totalFound": 0
                })
        except Exception as e:
            print(f"[ERROR] Lỗi khi bốc kết quả cho {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e),
                "dois": [],
                "totalFound": 0
            })
            
    session_result_dir = RESULT_DIR / session_id
    if session_result_dir.exists():
        try:
            shutil.rmtree(session_result_dir)
            print(f"[DEBUG] Đã dọn dẹp thư mục result cho session: {session_id}")
        except Exception as e:
            print(f"[ERROR] Không thể xóa thư mục result session {session_id}: {e}")

    return {"results": results}

@router.get("/test")
async def test_api():
    return {"status": "ok", "temporary_directory": str(TEMP_DIR)}
