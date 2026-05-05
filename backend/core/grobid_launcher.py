# grobid_launcher.py
from __future__ import annotations

import os
import socket
import subprocess
import time

import requests

GROBID_URL = "http://localhost:8070/api/isalive"
COMPOSE_PATH = os.getenv("GROBID_COMPOSE_PATH", os.path.join(os.getcwd(), "GrobidServer"))
IMAGE_NAME = "docker.io/lfoppiano/grobid:0.9.0"
CONTAINER_NAME = "grobidserver"
GROBID_PORT = 8070
POLL_INTERVAL = 2
MAX_RETRIES = 30


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def is_grobid_alive() -> bool:
    try:
        response = requests.get(GROBID_URL, timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _start_grobid() -> None:
    if os.path.exists(COMPOSE_PATH):
        print(f"[Grobid Launcher] Dang chay 'docker-compose up' tai {COMPOSE_PATH}...")
        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=COMPOSE_PATH,
            capture_output=True,
            check=False,
        )
        return

    print("[Grobid Launcher] Khong tim thay folder Compose, chay truc tiep bang Docker Run...")
    subprocess.Popen(
        [
            "docker",
            "run",
            "--name",
            CONTAINER_NAME,
            "-d",
            "--rm",
            "-p",
            f"{GROBID_PORT}:{GROBID_PORT}",
            IMAGE_NAME,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def init_grobid() -> bool:
    print("\n[Grobid Launcher] Dang kiem tra trang thai Grobid...")
    if is_grobid_alive():
        print("[Grobid Launcher] Grobid da san sang phuc vu.")
        return True

    if is_port_in_use(GROBID_PORT):
        print(f"[Grobid Launcher] LOI: Cong {GROBID_PORT} dang bi chiem dung.")
        return False

    print("[Grobid Launcher] Grobid chua chay. Dang tien hanh khoi dong...")
    try:
        _start_grobid()

        print("[Grobid Launcher] Dang nap Model AI (Toi da 60s)...")
        for i in range(MAX_RETRIES):
            if is_grobid_alive():
                print(f"[Grobid Launcher] Thanh cong! Grobid da khoi dong sau {i * POLL_INTERVAL}s.")
                return True

            time.sleep(POLL_INTERVAL)
            if i and i % 5 == 0:
                print(f"[Grobid Launcher] Van dang doi... ({i * POLL_INTERVAL}s).")

        print("[Grobid Launcher] QUA GIO: Grobid khoi dong qua lau.")
        return False
    except Exception as e:
        print(f"[Grobid Launcher] Loi khoi dong: {e}")
        return False


if __name__ == "__main__":
    if init_grobid():
        print("[Main] Bat dau trich xuat du lieu XML tu PDF.")