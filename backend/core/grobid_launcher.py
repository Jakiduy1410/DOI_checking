import subprocess
import time
import requests
import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def is_grobid_alive():
    try:
        # Check Grobid health endpoint
        response = requests.get("http://localhost:8070/api/isalive", timeout=2)
        return response.status_code == 200
    except:
        return False

def init_grobid():
    print("\n[Grobid Launcher] Checking Grobid status...")
    
    if is_grobid_alive():
        print("[Grobid Launcher] Grobid is already running and healthy.")
        return True

    if is_port_in_use(8070):
        print("[Grobid Launcher] Error: Port 8070 is in use but Grobid is not responding.")
        return False

    print("[Grobid Launcher] Grobid is not running. Attempting to start via Docker...")
    
    try:
        # Try to start a container named 'grobid' if it exists
        result = subprocess.run(["docker", "start", "grobid"], capture_output=True, text=True)
        if result.returncode == 0:
            print("[Grobid Launcher] Started existing 'grobid' container.")
        else:
            # If start fails, try to run a new one
            print("[Grobid Launcher] No existing 'grobid' container found. Running a new one...")
            # We use --rm to clean up, -d for detached, -p for port mapping
            # Using version 0.8.1 as a standard modern version
            subprocess.Popen([
                "docker", "run", 
                "--name", "grobid", 
                "-d", "--rm", 
                "--init", 
                "--ulimit", "core=0", 
                "-p", "8070:8070", 
                "grobid/grobid:0.9.0"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[Grobid Launcher] New Grobid container is starting in background.")

        # Wait for the service to be ready
        print("[Grobid Launcher] Waiting for Grobid to initialize (this may take up to 30s)...")
        max_retries = 30
        for i in range(max_retries):
            if is_grobid_alive():
                print("[Grobid Launcher] Grobid is READY!")
                return True
            time.sleep(2)
            if i % 5 == 0 and i > 0:
                print(f"[Grobid Launcher] Still waiting... ({i*2}s)")
        
        print("[Grobid Launcher] Timeout: Grobid did not start in time. Please check Docker manually.")
        return False

    except FileNotFoundError:
        print("[Grobid Launcher] Error: 'docker' command not found. Is Docker Desktop running?")
        return False
    except Exception as e:
        print(f"[Grobid Launcher] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    init_grobid()
