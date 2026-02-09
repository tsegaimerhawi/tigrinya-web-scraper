const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Newspaper {
  id: string;
  name: string;
  source: string;
  description: string;
}

export interface Article {
  index: number;
  news_title: string;
  article_url: string;
  publication_date: string;
  pdf_filename: string;
  pdf_url: string;
  word_count: number;
  processing_status: string;
}

export interface ArticleText extends Article {
  extracted_text: string;
  entities?: {
    people: string[];
    locations: string[];
    organizations: string[];
  };
  images?: {
    path: string;
    filename: string;
    page: number;
    description_tigrinya: string;
  }[];
}

export const api = {
  async getNewspapers(): Promise<Newspaper[]> {
    const res = await fetch(`${API_BASE}/newspapers`);
    const data = await res.json();
    return data.newspapers || [];
  },

  async getArticles(limit = 100, offset = 0): Promise<{ articles: Article[]; total: number }> {
    const res = await fetch(`${API_BASE}/articles?limit=${limit}&offset=${offset}`);
    return res.json();
  },

  async getArticleText(index: number): Promise<ArticleText> {
    const res = await fetch(`${API_BASE}/articles/${index}/text`);
    if (!res.ok) throw new Error('Article not found');
    return res.json();
  },

  async wordFrequency(text: string, topN = 50): Promise<{ word: string; count: number }[]> {
    const res = await fetch(`${API_BASE}/nlp/word-frequency`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, top_n: topN }),
    });
    const data = await res.json();
    return data.data || [];
  },

  async textStats(text: string): Promise<{
    char_count: number;
    word_count: number;
    line_count: number;
    geez_char_count: number;
  }> {
    const res = await fetch(`${API_BASE}/nlp/stats`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    return data.data || {};
  },

  async extractSentences(text: string, minLength = 10): Promise<string[]> {
    const res = await fetch(`${API_BASE}/nlp/sentences?min_length=${minLength}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    return data.data || [];
  },

  async dedupeLines(text: string): Promise<string> {
    const res = await fetch(`${API_BASE}/nlp/dedupe-lines`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    return data.data || '';
  },

  async askRag(
    question: string,
    k = 5,
    history?: { role: string; content: string }[]
  ): Promise<{ ok: boolean; answer: string; question: string }> {
    const res = await fetch(`${API_BASE}/rag/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, k, history: history ?? [] }),
    });
    return res.json();
  },

  async startScrape(params: { newspaper_id: string; max_articles: number; max_pages?: number }): Promise<{ ok: boolean; message?: string }> {
    const res = await fetch(`${API_BASE}/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ newspaper_id: params.newspaper_id, max_articles: params.max_articles, max_pages: params.max_pages ?? 100 }),
    });
    return res.json();
  },

  async getScrapeStatus(): Promise<{ running: boolean; stage: string | null; result?: any; error?: string }> {
    const res = await fetch(`${API_BASE}/scrape/status`);
    const data = await res.json();
    return { running: data.running, stage: data.stage ?? null, result: data.result, error: data.error };
  },

  async processAllPdfs(): Promise<{ ok: boolean; message?: string }> {
    const res = await fetch(`${API_BASE}/process/all`, { method: 'POST' });
    return res.json();
  },

  async getProcessingStatus(): Promise<{ running: boolean; stage: string | null; result?: any; error?: string }> {
    const res = await fetch(`${API_BASE}/process/status`);
    const data = await res.json();
    return { running: data.running, stage: data.stage ?? null, result: data.result, error: data.error };
  },

  async runIngest(): Promise<{ ok: boolean; count?: number; points_count?: number; collection?: string; error?: string }> {
    const res = await fetch(`${API_BASE}/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    return res.json();
  },

  async getQdrantStatus(): Promise<{ ok: boolean; collections?: { name: string; points_count: number }[]; error?: string }> {
    const res = await fetch(`${API_BASE}/pipeline/qdrant-status`);
    const data = await res.json();
    return { ok: data.ok, collections: data.collections, error: data.error };
  },

  async getValidate(): Promise<{ pdf_metadata_count: number; completed_downloads: number; raw_data_count: number; total_words: number }> {
    const res = await fetch(`${API_BASE}/pipeline/validate`);
    const data = await res.json();
    return {
      pdf_metadata_count: data.pdf_metadata_count ?? 0,
      completed_downloads: data.completed_downloads ?? 0,
      raw_data_count: data.raw_data_count ?? 0,
      total_words: data.total_words ?? 0,
    };
  },
};
