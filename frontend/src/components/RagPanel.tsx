import React, { useState } from 'react';
import { api } from '../api/client';

export default function RagPanel() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const res = await api.askRag(question.trim());
      if (res.ok && res.answer) {
        setAnswer(res.answer);
      } else {
        setError((res as any).error || 'No answer returned.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rag-panel">
      <h2>Ask Tigrinya (RAG)</h2>
      <p className="subtitle">
        Ask questions in Tigrinya or English. Answers use the ingested news corpus (run Scrape → Process → Llama Ingest first).
      </p>
      <div className="form-row">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. ኤርትራ እንታይ እያ? or What is Haddas Ertra?"
          rows={2}
          disabled={loading}
          className="rag-input"
        />
        <button
          onClick={handleAsk}
          disabled={loading || !question.trim()}
          className="btn-primary"
        >
          {loading ? 'Thinking…' : 'Ask'}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {answer && (
        <div className="rag-answer">
          <strong>Answer:</strong>
          <p className="answer-text">{answer}</p>
        </div>
      )}
    </div>
  );
}
