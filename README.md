# Tigrinya Scraper

A Python tool for scraping and processing Haddas Ertra Tigrinya newspapers from shabait.com.

## Features

- 🕷️ **Automated Scraping**: Downloads Haddas Ertra newspaper PDFs
- 📄 **Multi-page Navigation**: Handles pagination to access older articles
- 🔍 **Smart PDF Detection**: Locates download links using image-based navigation
- 🧹 **Text Cleaning**: Removes English words, navigation elements, and noise
- 🌍 **Ge'ez Script Focus**: Preserves only Tigrinya characters, numbers, and punctuation

## Installation

### Prerequisites

- Python 3.8+
- Git

### Step 1: Clone or Navigate to Project

```bash
cd tigrinya-scraper
```

### Step 2: Create Virtual Environment

```bash
python -m venv .env
source .env/bin/activate  # On Windows: .env\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Playwright Browsers

```bash
playwright install chromium
```

## Usage

### Step 1: Scrape and Download PDFs

```bash
python scraper.py
```

This will:
- Navigate to shabait.com and collect article URLs
- Download PDFs to the `pdfs/` directory
- Create `pdf_metadata.json` with download information

### Step 2: Process PDFs and Extract Text

```bash
python pdf_processor.py
```

This will:
- Extract text from all downloaded PDFs
- Clean the text (remove English, navigation elements, noise)
- Create `raw_data.json` with processed text data

## Output Files

- `pdf_metadata.json`: Metadata about downloaded PDFs (URLs, titles, dates, file paths)
- `raw_data.json`: Processed text data with cleaned Ge'ez script content
- `pdfs/`: Directory containing downloaded PDF files

## Configuration

You can modify the following in `scraper.py`:
- `max_articles`: Number of articles to download (default: 20)
- `max_pages`: Maximum pages to search (default: 50)
- Rate limiting delay between downloads (default: 4 seconds)

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
