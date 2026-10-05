import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["PYTHONPATH"] = BACKEND_DIR

import uvicorn

if __name__ == "__main__":
    print(f"[*] Starting AAROH FastAPI Backend from: {BACKEND_DIR}")
    print("[*] Target URL: http://127.0.0.1:8000")
    print("[*] Swagger API Docs: http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
