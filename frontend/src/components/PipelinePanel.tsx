import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function PipelinePanel() {
  const [scrapeStatus, setScrapeStatus] = useState<{ running: boolean; stage: string | null; result: any; error: string | null } | null>(null);
  const [processStatus, setProcessStatus] = useState<{ running: boolean; stage: string | null; result: any; error: string | null } | null>(null);
  const [ingestResult, setIngestResult] = useState<{ ok: boolean; count?: number; points_count?: number; collection?: string; error?: string } | null>(null);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [qdrantResult, setQdrantResult] = useState<{ ok: boolean; collections?: { name: string; points_count: number }[]; error?: string } | null>(null);
  const [validateResult, setValidateResult] = useState<{
    pdf_metadata_count: number;
    completed_downloads: number;
    raw_data_count: number;
    total_words: number;
  } | null>(null);
  const [scrapeLimit, setScrapeLimit] = useState(20);
  const [scrapeLoading, setScrapeLoading] = useState(false);
  const [processLoading, setProcessLoading] = useState(false);

  useEffect(() => {
    const poll = async () => {
      const [scrape, proc] = await Promise.all([api.getScrapeStatus(), api.getProcessingStatus()]);
      setScrapeStatus({
        running: scrape.running,
        stage: scrape.stage,
        result: scrape.result,
        error: scrape.error,
      });
      setProcessStatus({
        running: proc.running,
        stage: proc.stage,
        result: proc.result,
        error: proc.error,
      });
    };
    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleScrape = async () => {
    setScrapeLoading(true);
    try {
      await api.startScrape({
        newspaper_id: 'haddas-ertra',
        max_articles: Math.max(1, Math.min(500, scrapeLimit)),
        max_pages: 100,
      });
    } finally {
      setScrapeLoading(false);
    }
  };

  const handleProcessAll = async () => {
    setProcessLoading(true);
    try {
      await api.processAllPdfs();
    } finally {
      setProcessLoading(false);
    }
  };

  const handleIngest = async () => {
    setIngestLoading(true);
    setIngestResult(null);
    try {
      const res = await api.runIngest();
      setIngestResult(res);
    } finally {
      setIngestLoading(false);
    }
  };

  const handleCheckQdrant = async () => {
    const res = await api.getQdrantStatus();
    setQdrantResult(res);
  };

  const handleValidate = async () => {
    const res = await api.getValidate();
    setValidateResult(res);
  };

  return (
    <div className="pipeline-panel">
      <h2>Pipeline</h2>
      <p className="subtitle">
        Update the index whenever you want: Scrape → Process → Ingest. RAG answers from the stored vectors independently—run this only when you want to refresh the data. Then check Qdrant or validate.
      </p>

      <div className="pipeline-steps">
        <section className="pipeline-step">
          <h3>1. Scrape</h3>
          <p className="step-desc">Download Haddas Ertra PDFs.</p>
          <div className="step-actions">
            <input
              type="number"
              min={1}
              max={500}
              value={scrapeLimit}
              onChange={(e) => setScrapeLimit(Number(e.target.value) || 20)}
              className="step-input"
            />
            <button
              onClick={handleScrape}
              disabled={scrapeStatus?.running || scrapeLoading}
              className="btn-primary"
            >
              {scrapeStatus?.running || scrapeLoading ? 'Running…' : 'Start Scrape'}
            </button>
          </div>
          {(scrapeStatus?.stage || scrapeStatus?.result || scrapeStatus?.error) && (
            <div className={`step-status ${scrapeStatus?.error ? 'error' : ''}`}>
              {scrapeStatus?.running && <span>Stage: {scrapeStatus.stage}</span>}
              {scrapeStatus?.result && !scrapeStatus.running && (
                <span>Done: {scrapeStatus.result?.successful ?? 0} PDFs downloaded.</span>
              )}
              {scrapeStatus?.error && <span>Error: {scrapeStatus.error}</span>}
            </div>
          )}
        </section>

        <section className="pipeline-step">
          <h3>2. Process all PDFs</h3>
          <p className="step-desc">Extract text, NER, image descriptions → raw_data.json</p>
          <div className="step-actions">
            <button
              onClick={handleProcessAll}
              disabled={processStatus?.running || processLoading}
              className="btn-primary"
            >
              {processStatus?.running || processLoading ? 'Processing…' : 'Process all'}
            </button>
          </div>
          {(processStatus?.stage || processStatus?.result || processStatus?.error) && (
            <div className={`step-status ${processStatus?.error ? 'error' : ''}`}>
              {processStatus?.running && <span>Stage: {processStatus.stage}</span>}
              {processStatus?.result && !processStatus.running && (
                <span>Done: {processStatus.result?.processed ?? 0} processed, {processStatus.result?.total_words ?? 0} words.</span>
              )}
              {processStatus?.error && <span>Error: {processStatus.error}</span>}
            </div>
          )}
        </section>

        <section className="pipeline-step">
          <h3>3. Ingest to Qdrant</h3>
          <p className="step-desc">Embed raw_data with LlamaIndex and store in Qdrant (for RAG).</p>
          <div className="step-actions">
            <button onClick={handleIngest} disabled={ingestLoading} className="btn-primary">
              {ingestLoading ? 'Ingesting…' : 'Run ingest'}
            </button>
          </div>
          {ingestResult && (
            <div className={`step-status ${!ingestResult.ok ? 'error' : ''}`}>
              {ingestResult.ok ? (
                <span>Ingested {ingestResult.count} docs → {ingestResult.collection} ({ingestResult.points_count} points)</span>
              ) : (
                <span>Error: {ingestResult.error}</span>
              )}
            </div>
          )}
        </section>

        <section className="pipeline-step">
          <h3>Check Qdrant</h3>
          <p className="step-desc">Verify Qdrant is running and list collections.</p>
          <div className="step-actions">
            <button onClick={handleCheckQdrant} className="btn-secondary">
              Check Qdrant
            </button>
          </div>
          {qdrantResult && (
            <div className={`step-status ${!qdrantResult.ok ? 'error' : ''}`}>
              {qdrantResult.ok ? (
                <ul className="qdrant-list">
                  {qdrantResult.collections?.map((c) => (
                    <li key={c.name}>{c.name}: {c.points_count} points</li>
                  ))}
                  {(!qdrantResult.collections?.length) && <li>No collections</li>}
                </ul>
              ) : (
                <span>Error: {qdrantResult.error}</span>
              )}
            </div>
          )}
        </section>

        <section className="pipeline-step">
          <h3>Validate</h3>
          <p className="step-desc">Show counts for pdf_metadata and raw_data.</p>
          <div className="step-actions">
            <button onClick={handleValidate} className="btn-secondary">
              Validate
            </button>
          </div>
          {validateResult && (
            <div className="step-status">
              <span>Metadata: {validateResult.pdf_metadata_count} entries, {validateResult.completed_downloads} completed.</span>
              <span>raw_data: {validateResult.raw_data_count} articles, {validateResult.total_words} words.</span>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
