import requests

url = "http://127.0.0.1:8000/api/process"
file_path = "d:/Project/backend/temporary/test_upload.txt"

with open(file_path, "rb") as f:
    files = [("files", ("test_upload.txt", f, "text/plain"))]
    response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
