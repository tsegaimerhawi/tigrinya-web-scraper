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

export interface ScrapeStatus {
  running: boolean;
  stage: string | null;
  progress?: any;
  result: any;
  error: string | null;
}

export interface ScrapeRequest {
  newspaper_id: string;
  max_articles?: number;
  max_pages?: number;
  start_date?: string;
  end_date?: string;
}

export interface ProcessingStatus {
  ok: boolean;
  running: boolean;
  stage: string | null;
  result: any;
  error: string | null;
}

export const api = {
  async getNewspapers(): Promise<Newspaper[]> {
    const res = await fetch(`${API_BASE}/newspapers`);
    const data = await res.json();
    return data.newspapers || [];
  },

  async startScrape(req: ScrapeRequest): Promise<{ ok: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    return res.json();
  },

  async getScrapeStatus(): Promise<ScrapeStatus> {
    const res = await fetch(`${API_BASE}/scrape/status`);
    const data = await res.json();
    return {
      running: data.running || false,
      stage: data.stage || null,
      result: data.result || null,
      error: data.error || null,
    };
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

  async processPdfs(filenames: string[]): Promise<{ ok: boolean; message: string; count?: number }> {
    const res = await fetch(`${API_BASE}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames }),
    });
    return await res.json();
  },

  async getProcessingStatus(): Promise<ProcessingStatus> {
    const res = await fetch(`${API_BASE}/process/status`);
    return await res.json();
  },
};
