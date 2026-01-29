import React, { useState, useEffect } from 'react';
import { api, type ScrapeStatus } from '../api/client';

export default function ScrapePanel() {
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [status, setStatus] = useState<ScrapeStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const today = new Date().toISOString().split('T')[0];

  useEffect(() => {
    let interval: any;

    const poll = async () => {
      const s = await api.getScrapeStatus();
      setStatus(s);
      // Restart interval if we were expecting it to run but it hasn't caught up yet
      // or clear it if it's finished and we're not waiting for a start.
      if (!s.running && !loading) {
        clearInterval(interval);
      }
    };

    if (loading || status?.running) {
      interval = setInterval(poll, 2000);
    }

    return () => clearInterval(interval);
  }, [loading, status?.running]);

  const handleScrape = async () => {
    setLoading(true);
    // Show immediate feedback instead of clearing status
    setStatus({
      running: true,
      stage: 'starting',
      progress: null,
      result: null,
      error: null
    });

    try {
      await api.startScrape({
        newspaper_id: 'haddas-ertra',
        max_articles: 100,
        max_pages: 100,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });
    } catch (err) {
      console.error(err);
      setStatus({
        running: false,
        stage: 'error',
        progress: null,
        result: null,
        error: 'Failed to start scrape. Please check the backend is running.'
      });
    } finally {
      setLoading(false);
    }
  };

  const renderProgress = () => {
    if (!status?.progress) return null;
    const { stage, page, urls, current, total, url } = status.progress;

    if (stage === 'collecting') {
      return (
        <div className="progress-detail">
          <p className="pulse">🔍 Searching archive: Page {page}...</p>
          <p>Articles found: {urls}</p>
        </div>
      );
    }

    if (stage === 'downloading') {
      return (
        <div className="progress-detail">
          <p className="pulse">📥 Downloading: {current} / {total}</p>
          <div className="progress-bar-container">
            <div
              className="progress-bar"
              style={{ width: `${(current / total) * 100}%` }}
            ></div>
          </div>
          <p className="small-text">{url}</p>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="scrape-panel">
      <h2>Scrape Articles</h2>
      <p className="subtitle">Source: Haddas Ertra (shabait.com)</p>

      <div className="form-row">
        <div className="form-group">
          <label>Start Date:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            disabled={loading || status?.running}
            max={today}
          />
        </div>
        <div className="form-group">
          <label>End Date:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            disabled={loading || status?.running}
            max={today}
          />
        </div>
      </div>

      <button
        onClick={handleScrape}
        disabled={loading || status?.running}
        className="btn-primary"
      >
        {status?.running || loading ? 'Working...' : 'Start Scrape'}
      </button>

      {(status || loading) && (
        <div className="status-box">
          <p>
            <strong>Status:</strong> {status?.running || loading ? 'Active' : 'Idle'}
          </p>
          {status?.stage && <p className="stage">Stage: {status.stage.replace(/_/g, ' ')}</p>}

          {renderProgress()}

          {status?.result && !status.running && (
            <div className="result-summary">
              <p>
                ✅ Finished: {status.result.successful || 0} PDFs downloaded.
              </p>
            </div>
          )}
          {status?.error && <p className="error">❌ Error: {status.error}</p>}
        </div>
      )}

      {/* Downloaded PDFs Section */}
      <DownloadedPDFs />
    </div>
  );
}

// New component to show downloaded PDFs
function DownloadedPDFs() {
  const [pdfs, setPdfs] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    loadPdfs();
  }, []);

  const loadPdfs = async () => {
    setLoading(true);
    try {
      const response = await api.getArticles(20, 0);
      setPdfs(response.articles || []);
    } catch (err) {
      console.error('Failed to load PDFs:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="pdf-list-loading">Loading PDFs...</div>;
  if (pdfs.length === 0) return null;

  return (
    <div className="downloaded-pdfs">
      <h3>Recently Downloaded PDFs</h3>
      <div className="pdf-list">
        {pdfs.slice(0, 10).map((pdf) => (
          <div key={pdf.pdf_filename} className="pdf-item">
            <div className="pdf-info">
              <span className="pdf-name">{pdf.news_title || pdf.pdf_filename}</span>
              <span className="pdf-date">{pdf.publication_date}</span>
            </div>
            <span className={`pdf-status ${pdf.processing_status === 'completed' ? 'processed' : 'pending'}`}>
              {pdf.processing_status === 'completed' ? '✓ Processed' : '○ Downloaded'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
