import { useState, useEffect } from 'react';
import { api, type Article } from '../api/client';
import ArticleDetail from './ArticleDetail';

export default function ArticleList() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPdfs, setSelectedPdfs] = useState<Set<string>>(new Set());
  const [processing, setProcessing] = useState(false);

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

  const toggleSelection = (filename: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newSelected = new Set(selectedPdfs);
    if (newSelected.has(filename)) {
      newSelected.delete(filename);
    } else {
      newSelected.add(filename);
    }
    setSelectedPdfs(newSelected);
  };

  const handleProcessSelected = async () => {
    if (selectedPdfs.size === 0) return;

    setProcessing(true);
    try {
      const filenames = Array.from(selectedPdfs);
      await api.processPdfs(filenames);
      alert(`Processing ${filenames.length} PDFs. This may take a few minutes.`);
      setSelectedPdfs(new Set());
      // Reload articles after a delay to show updated status
      setTimeout(loadArticles, 2000);
    } catch (err) {
      console.error('Processing failed:', err);
      alert('Failed to start processing. Please try again.');
    } finally {
      setProcessing(false);
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

  const unprocessedArticles = articles.filter(a => a.processing_status !== 'completed');

  return (
    <div className="article-list">
      <div className="header">
        <h2>Articles ({articles.length})</h2>
        <div className="header-actions">
          {selectedPdfs.size > 0 && (
            <button
              onClick={handleProcessSelected}
              className="btn-primary"
              disabled={processing}
            >
              {processing ? 'Processing...' : `Process Selected (${selectedPdfs.size})`}
            </button>
          )}
          <button onClick={loadArticles} className="btn-secondary">
            Refresh
          </button>
        </div>
      </div>

      {unprocessedArticles.length > 0 && (
        <div className="info-banner">
          <p>💡 {unprocessedArticles.length} PDFs are downloaded but not yet processed. Select them below to extract text and run AI analysis.</p>
        </div>
      )}

      {articles.length === 0 ? (
        <p className="empty">No articles found. Start scraping to get articles.</p>
      ) : (
        <div className="articles-grid">
          {articles.map((article) => {
            const isProcessed = article.processing_status === 'completed';
            const isSelected = selectedPdfs.has(article.pdf_filename);

            return (
              <div
                key={article.index}
                className={`article-card ${isSelected ? 'selected' : ''}`}
                onClick={() => setSelectedIndex(article.index)}
              >
                {!isProcessed && (
                  <div className="checkbox-container" onClick={(e) => toggleSelection(article.pdf_filename, e)}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => { }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                )}

                <div className="card-content">
                  <div className="card-header">
                    <h3>{article.news_title || `Article ${article.index}`}</h3>
                    <span className={`status-badge ${isProcessed ? 'processed' : 'pending'}`}>
                      {isProcessed ? '✓ Processed' : '○ Downloaded'}
                    </span>
                  </div>
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
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
