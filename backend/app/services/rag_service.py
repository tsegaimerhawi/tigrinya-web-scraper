"""
RAG service: answer Tigrinya questions using retrieved context and Gemini.
"""
import os
from typing import Optional

from app.services.retriever_service import search


def _get_api_key() -> Optional[str]:
    from dotenv import load_dotenv
    from app.config import BASE_DIR
    load_dotenv(os.path.join(BASE_DIR, "config.env"))
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def answer(
    question: str,
    k: int = 5,
    collection_name: Optional[str] = None,
    qdrant_host: Optional[str] = None,
    qdrant_port: Optional[int] = None,
) -> str:
    """
    Answer a question using RAG: retrieve relevant chunks from Qdrant, then generate answer with Gemini.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    api_key = _get_api_key()
    if not api_key:
        return "Error: GEMINI_API_KEY or GOOGLE_API_KEY not set."

    docs = search(question, k=k, collection_name=collection_name, qdrant_host=qdrant_host, qdrant_port=qdrant_port)
    if not docs:
        return "I couldn't find any relevant documents to answer your question. Make sure ingestion has been run and Qdrant is available."

    context = "\n\n".join(
        f"[Source: {d.get('metadata', {}).get('news_title', 'Unknown')}]\n{d.get('text', '')}"
        for d in docs
    )

    template = """You are a helpful assistant for Tigrinya news and history.
Use the following retrieved context to answer the question.
If you don't know the answer, say so. Answer in the same language as the question (Tigrinya or English).

Context:
{context}

Question: {question}

Answer:"""
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
        max_output_tokens=2048,
        google_api_key=api_key,
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": question})
