"""FastAPI app for Tigrinya scraper frontend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import articles, nlp, newspapers, scrape, process, ingest, rag

app = FastAPI(
    title="Tigrinya Web Scraper API",
    description="Scrape Tigrinya news, extract text, run NLP.",
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
app.include_router(scrape.router)
app.include_router(process.router)
app.include_router(articles.router)
app.include_router(nlp.router)
app.include_router(ingest.router)
app.include_router(rag.router)


@app.get("/")
def root():
    return {"message": "Tigrinya Web Scraper API", "docs": "/docs"}
