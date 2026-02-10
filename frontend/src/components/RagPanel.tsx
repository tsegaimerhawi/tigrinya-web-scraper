import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';

export type ChatMessage = { role: 'user' | 'assistant'; content: string };

export default function RagPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    setError(null);
    const userMessage: ChatMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await api.askRag(text, 5, history);
      if (res.ok && res.answer != null) {
        setMessages((prev) => [...prev, { role: 'assistant', content: res.answer }]);
      } else {
        setError((res as { error?: string })?.error || 'No answer returned.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div className="rag-panel">
      <div className="rag-panel-header">
        <h2>Ask Tigrinya (RAG)</h2>
        <button
          type="button"
          onClick={handleClear}
          className="btn-secondary rag-clear-btn"
          disabled={messages.length === 0}
        >
          New conversation
        </button>
      </div>
      <p className="subtitle">
        Ask questions in Tigrinya or English. Answers use the <strong>current vector store</strong>—RAG is independent of the pipeline. Run the Pipeline tab whenever you want to update the index; RAG will keep using whatever is stored until then.
      </p>

      <div className="rag-chat">
        <div className="rag-messages">
          {messages.length === 0 && (
            <p className="rag-placeholder">Ask something to start the conversation…</p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`rag-message rag-message-${msg.role}`}>
              <span className="rag-message-role">{msg.role === 'user' ? 'You' : 'RAG'}</span>
              <div className="rag-message-content">{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="rag-message rag-message-assistant">
              <span className="rag-message-role">RAG</span>
              <div className="rag-message-content rag-typing">Thinking…</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="rag-form-row">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="e.g. ኤርትራ እንታይ እያ? or What is Haddas Ertra?"
            rows={2}
            disabled={loading}
            className="rag-input"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="btn-primary"
          >
            {loading ? '…' : 'Send'}
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
    </div>
  );
}
