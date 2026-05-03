import os
import requests

def process_pdfs():
    grobid_url = "http://localhost:8070/api/processReferences"
    input_dir = "backend/testing/document"
    output_dir = "backend/testing/tmp_result"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Nên dùng Session nếu xử lý nhiều file liên tục để tái sử dụng connection, chạy sẽ mượt hơn
    session = requests.Session()

    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"Processing {filename}...")

            with open(pdf_path, 'rb') as f:
                files = {'input': f}
                # Tick chọn cả consolidate và raw citation
                data = {
                    'consolidateCitations': '0', # Tắt tự động đối chiếu của Grobid
                    'includeRawCitations': '1'   # Bật lấy text thô để tự check cờ
                }
                
                try:
                    # Thêm timeout (ví dụ 60 giây) để tránh bị treo vô hạn nếu file PDF bị lỗi format
                    response = session.post(grobid_url, files=files, data=data, timeout=60)
                    
                    if response.status_code == 200:
                        output_filename = filename.replace(".pdf", ".xml")
                        output_path = os.path.join(output_dir, output_filename)
                        with open(output_path, 'w', encoding='utf-8') as out_f:
                            out_f.write(response.text)
                        print(f"Saved result to {output_path}")
                    else:
                        print(f"Error processing {filename}: {response.status_code} - {response.text}")
                except requests.exceptions.Timeout:
                    # Bắt riêng lỗi timeout để biết file nào đang làm Grobid bị đơ
                    print(f"Timeout when processing {filename}. Skipping...")
                except Exception as e:
                    print(f"Failed to connect to Grobid: {e}")

if __name__ == "__main__":
    process_pdfs()