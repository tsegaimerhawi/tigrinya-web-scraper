import { useState, useEffect } from 'react';
import { api, type Article } from '../api/client';
import ArticleDetail from './ArticleDetail';

export default function ArticleList() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    setLoading(true);
    try {
      const data = await api.getArticles(100, 0);
      setArticles(data.articles);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading articles...</div>;
  }

  if (selectedIndex !== null) {
    return (
      <ArticleDetail
        index={selectedIndex}
        onBack={() => setSelectedIndex(null)}
        onRefresh={loadArticles}
      />
    );
  }

  return (
    <div className="article-list">
      <div className="header">
        <h2>Articles ({articles.length})</h2>
        <button onClick={loadArticles} className="btn-secondary">
          Refresh
        </button>
      </div>
      {articles.length === 0 ? (
        <p className="empty">No articles found. Start scraping to get articles.</p>
      ) : (
        <div className="articles-grid">
          {articles.map((article) => (
            <div
              key={article.index}
              className="article-card"
              onClick={() => setSelectedIndex(article.index)}
            >
              <h3>{article.news_title || `Article ${article.index}`}</h3>
              <p className="meta">
                Date: {article.publication_date || 'Unknown'} • Words: {article.word_count || 0}
              </p>
              <a
                href={article.article_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="link"
              >
                View Source →
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
