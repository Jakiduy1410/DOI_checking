import subprocess
import time
import requests
import socket
import os

# --- CẤU HÌNH ---
GROBID_URL = "http://localhost:8070/api/isalive"
COMPOSE_PATH = r"D:\GrobidServer"  # Đường dẫn đến folder chứa docker-compose.yml
IMAGE_NAME = "lfoppiano/grobid:0.9.0"
CONTAINER_NAME = "grobidserver"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def is_grobid_alive():
    try:
        # Kiểm tra xem server đã sẵn sàng bóc tách XML chưa
        response = requests.get(GROBID_URL, timeout=2)
        return response.status_code == 200
    except:
        return False

def init_grobid():
    print(f"\n[Grobid Launcher] Dang kiem tra trang thai Grobid...")
    
    # 1. Nếu đã chạy rồi thì thôi
    if is_grobid_alive():
        print("[Grobid Launcher] Grobid da san sang phuc vu.")
        return True

    # 2. Kiểm tra xem có thằng nào đang chiếm cổng 8070 không
    if is_port_in_use(8070):
        print("[Grobid Launcher] LOI: Cong 8070 dang bi chiem dung.")
        return False

    print("[Grobid Launcher] Grobid chua chay. Dang tien hanh khoi dong...")
    try:
        # 3. Uu tien chay bang Docker Compose
        if os.path.exists(COMPOSE_PATH):
            print(f"[Grobid Launcher] Dang chay 'docker-compose up' tai {COMPOSE_PATH}...")
            subprocess.run(["docker-compose", "up", "-d"], cwd=COMPOSE_PATH, capture_output=True)
        else:
            # 4. Phuong an du phong: Chay truc tiep bang Docker Run
            print("[Grobid Launcher] Khong tim thay folder Compose, chay truc tiep bang Docker Run...")
            subprocess.Popen([
                "docker", "run", 
                "--name", CONTAINER_NAME, 
                "-d", "--rm", 
                "-p", "8070:8070", 
                IMAGE_NAME
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Cho doi Grobid san sang
        print("[Grobid Launcher] Dang nap Model AI (Toi da 60s)...")
        max_retries = 30 
        for i in range(max_retries):
            if is_grobid_alive():
                print(f"[Grobid Launcher] Thanh cong! Grobid da khoi dong sau {i*2}s.")
                return True
            time.sleep(2)
            if i % 5 == 0 and i > 0:
                print(f"[Grobid Launcher] Van dang doi... ({i*2}s).")
        
        print("[Grobid Launcher] QUA GIO: Grobid khoi dong qua lau. Vui long kiem tra Docker Desktop.")
        return False

    except Exception as e:
        print(f"[Grobid Launcher] Loi khoi dong: {e}")
        return False

if __name__ == "__main__":
    if init_grobid():
        print("[Main] Bat dau trich xuat du lieu XML tu PDF.")
        # Chen ma xu ly tep tai day