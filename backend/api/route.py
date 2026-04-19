from fastapi import APIRouter, UploadFile, File, Form
import os
import shutil
import json
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
    print(f"[DEBUG] Nhận được yêu cầu xử lý {len(files)} file.")
    
    for file in files:
        try:
            file_path = TEMP_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"[DEBUG] Đã lưu file: {file.filename}")
        except Exception as e:
            print(f"[ERROR] Lỗi khi lưu file {file.filename}: {e}")

    print(f"[DEBUG] Bắt đầu chạy pipeline cho toàn bộ file...")
    try:
        pipeline()
        print(f"[DEBUG] Pipeline đã hoàn thành.")
    except Exception as e:
        print(f"[ERROR] Pipeline gặp sự cố: {e}")
        return {"results": [{"filename": f.filename, "status": "error", "error": "Pipeline failure"} for f in files]}

    results = []
    for file in files:
        try:
            json_filename = f"{file.filename}.json"
            json_path = RESULT_DIR / json_filename
            
            print(f"[DEBUG] Đang tìm kết quả: {json_filename}")
            
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
                    
                    mapped_result["dois"].append({
                        "doi": ref.get("doi") or "N/A",
                        "valid": is_valid,
                        "title": ref.get("title"),
                        "authors": ref.get("authors"),
                        "journal": ref.get("venue"),
                        "year": ref.get("year"),
                        "url": f"https://doi.org/{ref.get('doi')}" if ref.get("doi") else "#",
                        "type": "Article",
                        "error": "Không tìm thấy DOI hợp lệ" if status == "invalid_doi" else None
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
            
    return {"results": results}

@router.get("/test")
async def test_api():
    return {"status": "ok", "temporary_directory": str(TEMP_DIR)}
