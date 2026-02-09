"""FastAPI app for Tigrinya News: articles and RAG only. Scraping and pipeline run separately (script_runner.py)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import articles, nlp, newspapers, rag, pipeline_runner, pipeline

app = FastAPI(
    title="Tigrinya News API",
    description="Browse articles and ask questions (RAG). Scraping and pipeline run via script_runner.py.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(newspapers.router)
app.include_router(articles.router)
app.include_router(nlp.router)
app.include_router(rag.router)
app.include_router(pipeline_runner.router)
app.include_router(pipeline.router)


@app.get("/")
def root():
    return {"message": "Tigrinya News API", "docs": "/docs"}
