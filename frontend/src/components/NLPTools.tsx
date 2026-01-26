import { useState } from 'react';
import { api } from '../api/client';

interface Props {
  text: string;
}

export default function NLPTools({ text }: Props) {
  const [wordFreq, setWordFreq] = useState<{ word: string; count: number }[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [sentences, setSentences] = useState<string[]>([]);
  const [deduped, setDeduped] = useState<string>('');
  const [loading, setLoading] = useState<string | null>(null);

  const runWordFreq = async () => {
    setLoading('wordfreq');
    try {
      const data = await api.wordFrequency(text, 50);
      setWordFreq(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(null);
    }
  };

  const runStats = async () => {
    setLoading('stats');
    try {
      const data = await api.textStats(text);
      setStats(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(null);
    }
  };

  const runSentences = async () => {
    setLoading('sentences');
    try {
      const data = await api.extractSentences(text, 10);
      setSentences(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(null);
    }
  };

  const runDedupe = async () => {
    setLoading('dedupe');
    try {
      const data = await api.dedupeLines(text);
      setDeduped(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="nlp-tools">
      <h3>NLP Analysis Tools</h3>
      <div className="nlp-buttons">
        <button
          onClick={runWordFreq}
          disabled={loading !== null}
          className="btn-secondary"
        >
          {loading === 'wordfreq' ? 'Loading...' : 'Word Frequency'}
        </button>
        <button
          onClick={runStats}
          disabled={loading !== null}
          className="btn-secondary"
        >
          {loading === 'stats' ? 'Loading...' : 'Text Statistics'}
        </button>
        <button
          onClick={runSentences}
          disabled={loading !== null}
          className="btn-secondary"
        >
          {loading === 'sentences' ? 'Loading...' : 'Extract Sentences'}
        </button>
        <button
          onClick={runDedupe}
          disabled={loading !== null}
          className="btn-secondary"
        >
          {loading === 'dedupe' ? 'Loading...' : 'Remove Duplicate Lines'}
        </button>
      </div>

      {wordFreq.length > 0 && (
        <div className="nlp-result">
          <h4>Top 50 Words</h4>
          <div className="word-freq-list">
            {wordFreq.map((item, i) => (
              <span key={i} className="word-tag">
                {item.word} ({item.count})
              </span>
            ))}
          </div>
        </div>
      )}

      {stats && (
        <div className="nlp-result">
          <h4>Text Statistics</h4>
          <ul>
            <li>Characters: {stats.char_count}</li>
            <li>Words: {stats.word_count}</li>
            <li>Lines: {stats.line_count}</li>
            <li>Ge'ez Characters: {stats.geez_char_count}</li>
          </ul>
        </div>
      )}

      {sentences.length > 0 && (
        <div className="nlp-result">
          <h4>Extracted Sentences ({sentences.length})</h4>
          <div className="sentences-list">
            {sentences.slice(0, 20).map((s, i) => (
              <p key={i}>{s}</p>
            ))}
            {sentences.length > 20 && <p>... and {sentences.length - 20} more</p>}
          </div>
        </div>
      )}

      {deduped && (
        <div className="nlp-result">
          <h4>Deduplicated Text</h4>
          <div className="text-box">
            <pre>{deduped}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
