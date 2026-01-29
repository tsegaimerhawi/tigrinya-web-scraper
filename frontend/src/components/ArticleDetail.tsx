import { useState, useEffect } from 'react';
import { api, type ArticleText } from '../api/client';
import NLPTools from './NLPTools';

interface Props {
  index: number;
  onBack: () => void;
  onRefresh: () => void;
}

export default function ArticleDetail({ index, onBack }: Props) {
  const [article, setArticle] = useState<ArticleText | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [showNLP, setShowNLP] = useState(false);

  useEffect(() => {
    loadArticle();
  }, [index]);

  const loadArticle = async () => {
    setLoading(true);
    try {
      const data = await api.getArticleText(index);
      setArticle(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const copyText = async () => {
    if (!article?.extracted_text) return;
    try {
      await navigator.clipboard.writeText(article.extracted_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="loading">Loading article...</div>;
  }

  if (!article) {
    return (
      <div>
        <button onClick={onBack} className="btn-secondary">
          ← Back
        </button>
        <p className="error">Article not found</p>
      </div>
    );
  }

  return (
    <div className="article-detail">
      <div className="header">
        <button onClick={onBack} className="btn-secondary">
          ← Back to List
        </button>
        <div className="actions">
          <button onClick={copyText} className="btn-primary">
            {copied ? '✓ Copied!' : 'Copy Text'}
          </button>
          <button onClick={() => setShowNLP(!showNLP)} className="btn-secondary">
            {showNLP ? 'Hide' : 'Show'} NLP Tools
          </button>
        </div>
      </div>
      <h1>{article.news_title}</h1>
      <div className="meta">
        <p>
          <strong>Date:</strong> {article.publication_date || 'Unknown'}
        </p>
        <p>
          <strong>Word Count:</strong> {article.word_count || 0}
        </p>
        <p>
          <strong>Source:</strong>{' '}
          <a href={article.article_url} target="_blank" rel="noopener noreferrer" className="link">
            {article.article_url}
          </a>
        </p>
      </div>
      {showNLP && article.extracted_text && (
        <NLPTools text={article.extracted_text} />
      )}

      {article.entities && (
        <div className="entities-section">
          <h2>Extracted Entities (AI Generated)</h2>
          <div className="entities-grid">
            <div className="entity-card">
              <h3>People</h3>
              <ul>
                {article.entities.people.length > 0 ? (
                  article.entities.people.map((p, i) => <li key={i}>{p}</li>)
                ) : (
                  <li className="empty">None found</li>
                )}
              </ul>
            </div>
            <div className="entity-card">
              <h3>Locations</h3>
              <ul>
                {article.entities.locations.length > 0 ? (
                  article.entities.locations.map((l, i) => <li key={i}>{l}</li>)
                ) : (
                  <li className="empty">None found</li>
                )}
              </ul>
            </div>
            <div className="entity-card">
              <h3>Organizations</h3>
              <ul>
                {article.entities.organizations.length > 0 ? (
                  article.entities.organizations.map((o, i) => <li key={i}>{o}</li>)
                ) : (
                  <li className="empty">None found</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {article.images && article.images.length > 0 && (
        <div className="images-section">
          <h2>Extracted Images</h2>
          <div className="images-grid">
            {article.images.map((img, i) => (
              <div key={i} className="image-card">
                <p className="image-description">
                  <strong>Description (Tigrinya):</strong> {img.description_tigrinya || 'No description generated'}
                </p>
                <p className="image-meta">Page {img.page}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-content">
        <h2>Extracted Text</h2>
        <div className="text-box">
          <pre>{article.extracted_text || 'No text available'}</pre>
        </div>
      </div>
    </div>
  );
}
