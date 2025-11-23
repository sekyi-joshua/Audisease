from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.predict import router as predict_router

app = FastAPI(
    title="AuDisease Backend",
    description="Backend API for Parkinson's voice screening.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "message": "AuDisease backend running"}
