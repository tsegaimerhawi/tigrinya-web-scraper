"""
RAG service: answer Tigrinya questions using retrieved context and Gemini.
Supports single-turn and multi-turn (conversation) answers.
"""
import os
from typing import Optional, List, Dict, Any

from app.services.retriever_service import search, RetrieverError


def _get_api_key() -> Optional[str]:
    from dotenv import load_dotenv
    from app.config import BASE_DIR
    load_dotenv(os.path.join(BASE_DIR, "config.env"))
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def answer(
    question: str,
    k: int = 5,
    history: Optional[List[Dict[str, str]]] = None,
    collection_name: Optional[str] = None,
    qdrant_host: Optional[str] = None,
    qdrant_port: Optional[int] = None,
) -> str:
    """
    Answer a question using RAG. If history is provided, uses it for multi-turn conversation.
    history: list of {"role": "user"|"assistant", "content": "..."}
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    api_key = _get_api_key()
    if not api_key:
        return "Error: GOOGLE_API_KEY (or GEMINI_API_KEY) not set."

    try:
        docs = search(question, k=k, collection_name=collection_name, qdrant_host=qdrant_host, qdrant_port=qdrant_port)
    except RetrieverError as e:
        return str(e)
    if not docs:
        return (
            "I couldn't find any relevant documents for that question. "
            "Make sure you've run the pipeline: Scrape → Process → Llama Ingest, and that Qdrant is running (e.g. docker run -p 6333:6333 qdrant/qdrant)."
        )

    context = "\n\n".join(
        f"[Source: {d.get('metadata', {}).get('news_title', 'Unknown')}]\n{d.get('text', '')}"
        for d in docs
    )

    system_text = """You are a helpful assistant for Tigrinya news and history.
Use the following retrieved context to answer the user. You may also use the conversation history for follow-up questions.
If you don't know the answer, say so. Answer in the same language as the question (Tigrinya or English).

Context:
""" + context

    messages: List[Any] = [SystemMessage(content=system_text)]

    if history:
        for h in history:
            role = (h.get("role") or "user").lower()
            content = h.get("content") or ""
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=question))

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
        max_output_tokens=2048,
        google_api_key=api_key,
    )
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)
