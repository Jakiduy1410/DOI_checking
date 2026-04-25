import httpx
import asyncio
from pathlib import Path
import json

async def test_upload_api():
    base_dir = Path(__file__).resolve().parent.parent
    
    # Bạn có thể đổi tên file ở đây để test thử các file khác nhau
    file_to_test = base_dir / "temporary" / "Check_1.pdf"
    
    if not file_to_test.exists():
        print(f"File không tồn tại: {file_to_test}")
        print("Vui lòng đảm bảo có file Check_1.pdf trong thư mục temporary")
        return
        
    url = "http://127.0.0.1:8000/process"
    
    print(f"Bắt đầu gửi file {file_to_test.name} lên API: {url}")
    
    async with httpx.AsyncClient(timeout=300) as client:
        with open(file_to_test, "rb") as f:
            files = [('files', (file_to_test.name, f, 'application/pdf'))]
            try:
                response = await client.post(url, files=files)
                print(f"\nStatus Code: {response.status_code}")
                print("Response JSON:")
                print(json.dumps(response.json(), indent=4, ensure_ascii=False))
            except Exception as e:
                print(f"Lỗi khi gọi API: {e}")
                print("Đảm bảo bạn đã chạy server bằng lệnh: uvicorn main:app --reload")

if __name__ == "__main__":
    asyncio.run(test_upload_api())
