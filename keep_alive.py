import requests
import time
import threading

def keep_alive():
    while True:
        try:
            requests.get("https://universal-download.onrender.com", timeout=5)
            print("✅ Pinged to keep awake")
        except:
            print("⚠️  Ping failed")
        time.sleep(600)  # 10 minutes

if __name__ == "__main__":
    thread = threading.Thread(target=keep_alive)
    thread.daemon = True
    thread.start()
    
    # Keep main thread alive
    while True:
        time.sleep(1)
