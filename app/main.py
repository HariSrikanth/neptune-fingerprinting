# Main Entrypoint

from fastapi import FastAPI
from app.routes.audio import router as audio_router

app = FastAPI(title="Audio Fingerprint API")

app.include_router(audio_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}