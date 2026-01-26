# Tigrinya Web Scraper

A full-stack web application for scraping and processing Tigrinya news articles from shabait.com, with a React frontend and FastAPI backend.

## Features

- 🕷️ **Automated Scraping**: Downloads Haddas Ertra newspaper PDFs
- 📄 **Multi-page Navigation**: Handles pagination to access older articles
- 🔍 **Smart PDF Detection**: Locates download links using image-based navigation
- 🧹 **Text Cleaning**: Removes English words, navigation elements, and noise
- 🌍 **Ge'ez Script Focus**: Preserves only Tigrinya characters, numbers, and punctuation
- 🌐 **Web Interface**: Modern React frontend for easy scraping and article management
- 📊 **NLP Tools**: Word frequency, text statistics, sentence extraction, and more
- 📋 **Copy Text**: Easy one-click copy of extracted article text

## Prerequisites

Before running the application, make sure you have:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+ and npm** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/downloads)

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

The startup scripts will handle installation automatically, or you can install manually:

**Backend Dependencies:**
```bash
python3 -m venv .env
source .env/bin/activate  # On Windows: .env\Scripts\activate
pip install -r backend/requirements.txt
playwright install chromium
```

**Frontend Dependencies:**
```bash
cd frontend
npm install
cd ..
```

### Configuration (Optional)

- **Backend API URL**: Edit `frontend/.env` if backend runs on a different port (default: `http://localhost:8000`)
- **Data Directory**: Set `TIGRINYA_DATA_DIR` environment variable to change where PDFs and metadata are stored

## Quick Start

### Option 1: Using Startup Scripts (Easiest)

**Terminal 1 - Start Backend:**
```bash
./start-backend.sh
```

**Terminal 2 - Start Frontend:**
```bash
./start-frontend.sh
```

The scripts will automatically:
- Create virtual environment if needed
- Install all dependencies
- Start the servers

### Option 2: Manual Setup

**Terminal 1 - Backend:**
```bash
# Create virtual environment
python3 -m venv .env
source .env/bin/activate  # On Windows: .env\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
playwright install chromium

# Start backend server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
# Install dependencies
cd frontend
npm install

# Start frontend server
npm run dev
```

### Access the Application

Once both servers are running:

- **Web Application**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000

### Using the Web Interface

1. **Scrape Articles:**
   - Go to the "Scrape" tab
   - Select a newspaper from the dropdown
   - Set the maximum number of articles
   - Click "Start Scrape"
   - Wait for the scraping to complete (status updates in real-time)

2. **View Articles:**
   - Go to the "Articles" tab
   - Browse the list of scraped articles
   - Click on any article to view details

3. **Copy Text & NLP Analysis:**
   - Open an article detail view
   - Click "Copy Text" to copy all extracted text to clipboard
   - Click "Show NLP Tools" to analyze the text:
     - Word frequency analysis
     - Text statistics (character count, word count, etc.)
     - Sentence extraction
     - Remove duplicate lines

### Command Line (Legacy)

You can still use the original CLI scripts:

**Scrape and Download PDFs:**
```bash
python scraper.py
```

**Process PDFs and Extract Text:**
```bash
python pdf_processor.py
```

## Output Files

- `pdf_metadata.json`: Metadata about downloaded PDFs (URLs, titles, dates, file paths)
- `raw_data.json`: Processed text data with cleaned Ge'ez script content
- `pdfs/`: Directory containing downloaded PDF files

## API Endpoints

The FastAPI backend provides the following endpoints:

- `GET /newspapers` - List available newspapers
- `POST /scrape` - Start scraping articles
- `GET /scrape/status` - Get scraping status
- `GET /articles` - List processed articles
- `GET /articles/{index}/text` - Get full text of an article
- `POST /nlp/word-frequency` - Get word frequency analysis
- `POST /nlp/stats` - Get text statistics
- `POST /nlp/sentences` - Extract sentences
- `POST /nlp/dedupe-lines` - Remove duplicate lines

See http://localhost:8000/docs for interactive API documentation.

## Configuration

**Backend:**
- Modify `backend/app/config.py` to add more newspapers or change data directory
- Default data directory: project root (can be set via `TIGRINYA_DATA_DIR` env var)

**Frontend:**
- API URL: Set in `frontend/.env` (default: `http://localhost:8000`)

## Text Cleaning

The `pdf_processor.py` script performs extensive cleaning:
- Removes English words
- Removes navigation elements (bullets, symbols)
- Removes page numbers, dates, URLs
- Keeps only Ge'ez script characters (U+1200-U+137F), numbers, and standard punctuation
- Filters out lines with too many special characters

## License

This project is for educational and research purposes. Please respect website terms of service and copyright laws when using the scraped content.

## Author

Tsegai Merhawi - Tigrinya newspaper digitization project
