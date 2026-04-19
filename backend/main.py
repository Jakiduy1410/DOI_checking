from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.route import router as api_router
from pathlib import Path

app = FastAPI(title="DOI Checker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

BASE_DIR = Path(__file__).resolve().parent


STATIC_DIR = BASE_DIR.parent / "frontend" / "src" / "public"
VIEWS_DIR = BASE_DIR.parent / "frontend" / "src" / "views"

@app.get("/")
async def get_index():
    index_file = VIEWS_DIR / "index.html" 
 
    if index_file.exists():
        return FileResponse(index_file)

    return 
    {
        "error": "Vẫn chưa thấy index.html đâu Bibi ơi!",
        "check_tai_day": str(index_file)
    }


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)