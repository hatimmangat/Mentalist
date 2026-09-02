import os
from dotenv import load_dotenv

# Must run before any other app module is imported: several modules (e.g.
# app.llm.groq_client) read environment variables at import time, so if we
# load .env after those imports, they'd already have missed it.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth_router, chat_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mentalist API",
    description="A RAG-powered supportive listening companion, Jane. Real backend, real auth, real vector retrieval.",
    version="1.0.0",
)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(chat_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
