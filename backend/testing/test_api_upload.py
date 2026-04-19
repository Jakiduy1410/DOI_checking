import requests

url = "http://localhost:8000/api/upload"
file_path = "d:/Project/backend/temporary/test_file.txt"

with open(file_path, "rb") as f:
    files = {"file": ("uploaded_test.txt", f)}
    response = requests.post(url, files=files)

print(response.json())
