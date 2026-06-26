from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.analysis import router as analysis_router
import uvicorn
from config import settings

app = FastAPI(
    title=settings.APP_NAME
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": settings.APP_NAME
    }

app.include_router(analysis_router)
@app.get("/api/health")
async def health():
    return {
        "status": "healthy"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )