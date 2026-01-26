import { useState, useEffect } from 'react';
import { api, type Newspaper, type ScrapeStatus } from '../api/client';

export default function ScrapePanel() {
  const [newspapers, setNewspapers] = useState<Newspaper[]>([]);
  const [selectedNewspaper, setSelectedNewspaper] = useState<string>('');
  const [maxArticles, setMaxArticles] = useState(20);
  const [status, setStatus] = useState<ScrapeStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getNewspapers().then((data) => {
      setNewspapers(data);
      if (data.length > 0 && !selectedNewspaper) {
        setSelectedNewspaper(data[0].id);
      }
    });
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      const s = await api.getScrapeStatus();
      setStatus(s);
      if (!s.running) {
        clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleScrape = async () => {
    if (!selectedNewspaper) return;
    setLoading(true);
    try {
      await api.startScrape({
        newspaper_id: selectedNewspaper,
        max_articles: maxArticles,
        max_pages: 50,
      });
      const s = await api.getScrapeStatus();
      setStatus(s);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scrape-panel">
      <h2>Scrape Articles</h2>
      <div className="form-group">
        <label>Newspaper:</label>
        <select
          value={selectedNewspaper}
          onChange={(e) => setSelectedNewspaper(e.target.value)}
          disabled={loading || status?.running}
        >
          {newspapers.map((np) => (
            <option key={np.id} value={np.id}>
              {np.name} ({np.source})
            </option>
          ))}
        </select>
      </div>
      <div className="form-group">
        <label>Max Articles:</label>
        <input
          type="number"
          value={maxArticles}
          onChange={(e) => setMaxArticles(parseInt(e.target.value) || 20)}
          min={1}
          max={100}
          disabled={loading || status?.running}
        />
      </div>
      <button
        onClick={handleScrape}
        disabled={loading || status?.running || !selectedNewspaper}
        className="btn-primary"
      >
        {status?.running ? 'Scraping...' : 'Start Scrape'}
      </button>
      {status && (
        <div className="status-box">
          <p>
            <strong>Status:</strong> {status.running ? 'Running' : 'Idle'}
          </p>
          {status.stage && <p>Stage: {status.stage}</p>}
          {status.result && (
            <div>
              <p>
                Result: {status.result.successful || 0}/{status.result.total || 0} articles scraped
              </p>
            </div>
          )}
          {status.error && <p className="error">Error: {status.error}</p>}
        </div>
      )}
    </div>
  );
}
