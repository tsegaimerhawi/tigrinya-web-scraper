# 📰 Tigrinya News

**Browse Haddas Ertra and ask questions in Tigrinya or English—powered by RAG and the Ge'ez script.**

A full pipeline for **Tigrinya news**: scrape PDFs from [Haddas Ertra](https://shabait.com/category/newspapers/haddas-ertra-news), extract and clean Ge'ez text, embed with **LlamaIndex** + **Gemini**, store in **Qdrant**, and query via a **React + FastAPI** app. Built for researchers, linguists, and anyone working with Tigrinya NLP and low-resource language tech.

---

## ✨ What You Can Do

| **In the app** | **In Script Runner** |
|----------------|----------------------|
| 📖 Browse scraped articles with full text and metadata | 🕷️ Download Haddas Ertra PDFs (configurable limit) |
| 📋 Copy text, run word frequency, stats, sentence extraction | 📄 Extract Ge'ez text, NER, image descriptions → `raw_data.json` |
| 🤖 **Ask questions in Tigrinya or English**—answers from the ingested corpus (RAG) | 📦 Ingest into Qdrant (LlamaIndex + Gemini embeddings) |
| 🔍 Semantic search over the news corpus | ✅ Check Qdrant, validate metadata and raw data |

The **app** (React + FastAPI) is for **reading and asking**. The **Script Runner** (or CLI) is for **scraping, processing, and ingesting**. Run the pipeline once (or periodically), then use the app to explore and query.

---

## 🏗️ How It Fits Together

```
┌─────────────────────────────────────────────────────────────────┐
│  Script Runner (port 8765) or CLI                                 │
│  scraper.py → pdf_processor.py → llama_ingest.py                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
              pdf_metadata.json   raw_data.json   Qdrant
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  App (backend :8000 + frontend :5173)                           │
│  Articles (browse, copy, NLP tools)  +  Ask (RAG)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

- **Frontend:** React, TypeScript, Vite  
- **Backend:** FastAPI, Python 3.8+  
- **Scraping:** Playwright, pdfplumber  
- **NLP / RAG:** Google Gemini (embeddings + chat), LlamaIndex, Qdrant  
- **Data:** Ge'ez-focused text cleaning, sentence splitting, optional NER and image descriptions  

Inspired by the pipeline in [tigrinya-agent](https://github.com/tsegaimerhawi/tigrinya-agent).

---

## 🚀 Quick Start

### 1. Clone and install

```bash
git clone https://github.com/tsegaimerhawi/tigrinya-web-scraper.git
cd tigrinya-web-scraper
python3 -m venv .env
source .env/bin/activate   # Windows: .env\Scripts\activate
pip install -r backend/requirements.txt
playwright install chromium
cd frontend && npm install && cd ..
```

### 2. Configure

- Copy `config.env.example` → `config.env`
- Set **GEMINI_API_KEY** (or **GOOGLE_API_KEY**) for NER, image descriptions, and RAG  
- Optional: start **Qdrant** for RAG: `docker run -p 6333:6333 qdrant/qdrant`

### 3. Run the app (browse + ask)

```bash
# Terminal 1 – backend
./start-backend.sh
# or: cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 – frontend
./start-frontend.sh
# or: cd frontend && npm run dev
```

Open **http://localhost:5173** → **Articles** and **Ask (RAG)**.

### 4. (Optional) Run the pipeline (scrape → process → ingest)

```bash
python script_runner.py
```

Open **http://localhost:8765**. Use **Configuration**, then run **Scraper** → **PDF Processor** → **Llama Ingest**. After that, the app can show articles and answer questions from the ingested corpus.

---

## 📁 Project Layout

```
tigrinya-scraper/
├── backend/                 # FastAPI app (articles, NLP, RAG)
│   ├── app/
│   │   ├── routes/          # articles, nlp, rag
│   │   └── services/        # ingest, retriever, rag, pdf, etc.
│   └── requirements.txt
├── frontend/                # React app (Articles + Ask)
│   └── src/
│       ├── components/      # ArticleList, ArticleDetail, RagPanel, NLPTools
│       └── api/
├── script_runner.py         # Pipeline UI (scrape, process, ingest)
├── scraper.py               # CLI: download Haddas Ertra PDFs
├── pdf_processor.py         # CLI: extract & clean text, NER, images
├── llama_ingest.py          # CLI: raw_data → Qdrant (LlamaIndex)
├── runner_config.json       # Script Runner settings
├── config.env.example       # API keys and env template
└── README.md
```

---

## 📖 App Features (Articles + RAG)

- **Articles**  
  List from `raw_data.json`, open for full text. Copy to clipboard, run **NLP tools**: word frequency, character/word counts, sentence extraction, dedupe lines.

- **Ask (RAG)**  
  Type a question in **Tigrinya** or **English**. The app retrieves relevant chunks from Qdrant and generates an answer with Gemini. Example: *ኤርትራ እንታይ እያ?* or *What is Haddas Ertra?*

---

## 🔧 Script Runner (Pipeline)

| Step | What it does |
|------|----------------|
| **Scraper** | Fetches Haddas Ertra PDFs from shabait.com (limit in config). |
| **PDF Processor** | Extracts text, keeps Ge'ez script, runs NER and image descriptions → `raw_data.json`. |
| **Llama Ingest** | Builds sentence-level docs, embeds with Gemini, stores in Qdrant. |
| **Check Qdrant** | Tests connection and lists collections/point counts. |
| **Validate** | Shows counts for `pdf_metadata.json` and `raw_data.json`. |

Configuration (scraper limit, Qdrant host/port, collection, batch sizes) is in the UI or `runner_config.json`.

---

## 🌐 API (App backend)

The app backend exposes **articles**, **NLP**, and **RAG** only (no scrape/process/ingest):

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/newspapers` | List newspapers |
| GET | `/articles` | List articles (paginated) |
| GET | `/articles/{index}/text` | Full text for one article |
| POST | `/nlp/word-frequency`, `/nlp/stats`, `/nlp/sentences`, `/nlp/dedupe-lines` | NLP helpers |
| POST | `/rag/ask` | RAG answer (body: `{"question": "...", "k": 5}`) |
| POST | `/rag/search` | Semantic search only |

Interactive docs: **http://localhost:8000/docs**.

---

## ⚙️ Configuration

| Where | Purpose |
|-------|---------|
| `config.env` | `GEMINI_API_KEY` or `GOOGLE_API_KEY`; optional `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION` |
| `frontend/.env` | `VITE_API_URL` (default `http://localhost:8000`) |
| `runner_config.json` | Scraper limit, Qdrant settings, batch sizes (Script Runner) |
| `TIGRINYA_DATA_DIR` | Data directory (default: project root) |

---

## 📜 Text Processing (Ge'ez)

The pipeline keeps **Ge'ez script** (U+1200–U+137F), numbers, and punctuation. It strips:

- English words and navigation clutter  
- Page numbers, URLs, copyright text  
- Lines that are mostly symbols  

So you get clean Tigrinya text for analysis and RAG.

---

## 📄 Output Files

- **`pdf_metadata.json`** – Downloaded PDFs (URLs, titles, dates, paths)  
- **`raw_data.json`** – Processed articles (extracted text, word count, NER, image descriptions)  
- **`pdfs/`** – Downloaded PDF files  
- **`runner_config.json`** – Script Runner configuration  

---

## 📜 License

For educational and research use. Please respect the source site’s terms of service and copyright when using scraped content.

---

## 👤 Author

**Tsegai Merhawi** – Tigrinya newspaper digitization and NLP ([tigrinya-agent](https://github.com/tsegaimerhawi/tigrinya-agent))
