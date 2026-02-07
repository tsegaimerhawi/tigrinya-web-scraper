# Tigrinya Web Scraper

A full-stack web application for scraping and processing Tigrinya news articles from shabait.com, with a React frontend and FastAPI backend. Includes **LlamaIndex** ingestion into **Qdrant** and **RAG** to answer Tigrinya questions (similar to [tigrinya-agent](https://github.com/tsegaimerhawi/tigrinya-agent)).

## Features

- 🕷️ **Automated Scraping**: Downloads Haddas Ertra newspaper PDFs
- 📄 **Multi-page Navigation**: Handles pagination to access older articles
- 🔍 **Smart PDF Detection**: Locates download links using image-based navigation
- 🧹 **Text Cleaning**: Removes English words, navigation elements, and noise
- 🌍 **Ge'ez Script Focus**: Preserves only Tigrinya characters, numbers, and punctuation
- 🌐 **Web Interface**: Modern React frontend for scraping, articles, and RAG Q&A
- 📊 **NLP Tools**: Word frequency, text statistics, sentence extraction, and more
- 📋 **Copy Text**: Easy one-click copy of extracted article text
- 📦 **LlamaIndex + Qdrant**: Store processed text as embeddings in a vector database
- 🤖 **RAG**: Ask questions in Tigrinya or English; answers use the ingested news corpus
- 🖥️ **Script Runner UI**: Separate dashboard (port 8765) to run Scrape → Process → Ingest with live output and configuration (like [tigrinya-agent](https://github.com/tsegaimerhawi/tigrinya-agent))

## Prerequisites

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+ and npm** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Qdrant** (optional, for RAG): run with Docker: `docker run -p 6333:6333 qdrant/qdrant`
- **Google Gemini API key** (for NER, image descriptions, RAG embeddings and answers): set in `config.env` as `GEMINI_API_KEY` or `GOOGLE_API_KEY`

Verify installations:
```bash
python3 --version  # Should be 3.8 or higher
node --version     # Should be 18 or higher
npm --version
```

## Installation

### Clone the Repository

```bash
git clone https://github.com/tsegaimerhawi/tigrinya-web-scraper.git
cd tigrinya-web-scraper
```

### Install Dependencies

**Backend:**
```bash
python3 -m venv .env
source .env/bin/activate   # On Windows: .env\Scripts\activate
pip install -r backend/requirements.txt
playwright install chromium
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### Configuration

- Copy `config.env.example` to `config.env` and set **GEMINI_API_KEY** (or **GOOGLE_API_KEY**) for Gemini.
- Optional: set **QDRANT_HOST**, **QDRANT_PORT**, **QDRANT_COLLECTION** if not using defaults (localhost:6333, collection `tigrinya_llamaindex`).
- **Frontend API URL**: Edit `frontend/.env` if the backend runs on a different port (default: `http://localhost:8000`).
- **Data directory**: Set `TIGRINYA_DATA_DIR` to change where PDFs and `raw_data.json` are stored (default: project root).

## Quick Start

### Option 1: Startup Scripts

**Terminal 1 – Backend:**
```bash
./start-backend.sh
```

**Terminal 2 – Frontend:**
```bash
./start-frontend.sh
```

Then open **http://localhost:5173** for the main app and use the **Scrape**, **Articles**, and **Ask (RAG)** tabs.

### Option 2: Script Runner UI (Scrape → Process → Ingest)

Run the standalone Script Runner (similar to [tigrinya-agent](https://github.com/tsegaimerhawi/tigrinya-agent)):

```bash
source .env/bin/activate
pip install -r backend/requirements.txt
python script_runner.py
```

Open **http://localhost:8765**. You can:

- **Configuration** – Set scraper limit, Qdrant host/port, collection name, batch sizes (saved to `runner_config.json`).
- **Scraper** – Download Haddas Ertra PDFs (uses `--limit` from config).
- **PDF Processor** – Extract and clean text from PDFs; writes `raw_data.json`.
- **Llama Ingest** – Ingest `raw_data.json` into Qdrant with LlamaIndex (Gemini embeddings).
- **Check Qdrant** – Verify Qdrant is running and list collections.
- **Validate Results** – Check `pdf_metadata.json` and `raw_data.json` counts.

Output streams in real time. Use this UI to scrape, preprocess, extract, and store news data without running the React app.

### Option 3: Manual Backend + Frontend

**Terminal 1 – Backend:**
```bash
source .env/bin/activate
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 – Frontend:**
```bash
cd frontend
npm run dev
```

### RAG (Ask Tigrinya Questions)

1. **Ingest data** (once): Use the Script Runner UI (Llama Ingest) or call `POST /ingest` (or run `python llama_ingest.py` from project root). Ensure Qdrant is running and `raw_data.json` exists (run Scraper + PDF Processor first).
2. **Ask questions**: In the main app, open the **Ask (RAG)** tab and type a question in Tigrinya or English; answers are generated from the ingested corpus using Gemini.

You can also call the API directly: `POST /rag/ask` with body `{"question": "ኤርትራ እንታይ እያ?", "k": 5}`.

## Output Files

- `pdf_metadata.json` – Metadata about downloaded PDFs (URLs, titles, dates, file paths)
- `raw_data.json` – Processed text data with cleaned Ge'ez script content (used by Llama Ingest)
- `pdfs/` – Directory containing downloaded PDF files
- `runner_config.json` – Script Runner configuration (scraper limit, Qdrant, batch sizes)

## API Endpoints

- `GET /newspapers` – List available newspapers
- `POST /scrape` – Start scraping articles
- `GET /scrape/status` – Get scraping status
- `POST /process` – Run PDF processing (extract text, NER, image descriptions)
- `GET /process/status` – Get processing status
- `GET /articles` – List processed articles
- `GET /articles/{index}/text` – Get full text of an article
- `POST /nlp/word-frequency`, `POST /nlp/stats`, `POST /nlp/sentences`, `POST /nlp/dedupe-lines` – NLP utilities
- **Ingest & RAG**
  - `POST /ingest` – Run LlamaIndex ingestion (raw_data.json → Qdrant)
  - `POST /rag/ask` – Answer a question using RAG (body: `{"question": "...", "k": 5}`)
  - `POST /rag/search` – Semantic search only (body: `{"query": "...", "k": 5}`)

See **http://localhost:8000/docs** for interactive API documentation.

## Configuration

- **Backend**: `backend/app/config.py` – newspapers, data paths, Qdrant host/port/collection.
- **Frontend**: `frontend/.env` – API base URL (default `http://localhost:8000`).
- **Script Runner**: Use the Configuration button in the Script Runner UI, or edit `runner_config.json`.
- **Secrets**: `config.env` – `GEMINI_API_KEY` or `GOOGLE_API_KEY`; optional `QDRANT_*` overrides.

## Text Cleaning

The PDF processor (and backend `pdf_service`) clean text by:

- Removing English words and navigation elements (bullets, symbols)
- Removing page numbers, dates, URLs
- Keeping only Ge'ez script characters (U+1200–U+137F), numbers, and standard punctuation
- Filtering out lines with too many special characters

## License

This project is for educational and research purposes. Please respect website terms of service and copyright laws when using the scraped content.

## Author

Tsegai Merhawi – Tigrinya newspaper digitization project
