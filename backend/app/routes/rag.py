"""RAG API: ask Tigrinya questions over the ingested corpus."""
from typing import Optional, List

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag_service import answer as rag_answer
from app.services.retriever_service import search

router = APIRouter(prefix="/rag", tags=["rag"])


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class AskRequest(BaseModel):
    question: str
    k: int = 5
    history: Optional[List[ChatMessage]] = None


class SearchRequest(BaseModel):
    query: str
    k: int = 5


@router.post("/ask")
def ask(req: AskRequest):
    """Answer a question using RAG. Send optional history for multi-turn conversation."""
    history_dicts = [{"role": m.role, "content": m.content} for m in (req.history or [])]
    response = rag_answer(question=req.question, k=req.k, history=history_dicts or None)
    return {"ok": True, "answer": response, "question": req.question}


@router.post("/search")
def rag_search(req: SearchRequest):
    """Semantic search only (no LLM). Returns top-k chunks."""
    results = search(query=req.query, k=req.k)
    return {"ok": True, "results": results}
