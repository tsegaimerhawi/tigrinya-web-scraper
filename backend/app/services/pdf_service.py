"""PDF processing: extract and clean Ge'ez text."""
import json
import os
import re
from typing import Tuple, List, Dict
import pdfplumber

from app.config import METADATA_PATH, RAW_DATA_PATH, PDFS_DIR
from app.services import ai_processor

def deduplicate_geez_chars(text: str) -> str:
    """Fix character repetition in Ge'ez text (e.g., 'ክክብብ' -> 'ክብ')."""
    if not text:
        return ""
    
    # Simple regex to find repeated characters and replace with one
    # Note: Only applying to Ge'ez range \u1200-\u137F to be safe
    # This replaces sequences like AA with A
    result = ""
    if len(text) > 0:
        result += text[0]
        for i in range(1, len(text)):
            # If current char is same as previous and is in Ge'ez range, skip it
            is_geez = "\u1200" <= text[i] <= "\u137F"
            if is_geez and text[i] == text[i-1]:
                continue
            result += text[i]
    return result

def clean_text(text: str) -> str:
    """Clean extracted text: keep Ge'ez, numbers, punctuation; remove English and noise."""
    if not text:
        return ""

    noise = [
        r"PAGE\s+\d+", r"page\s+\d+", r"waga\s+[\d.]+", r"ዋጋ\s+[\d.]+",
        r"ISSUE\s+\d+", r"VOL\s+\d+", r"VOLUME\s+\d+",
        r"\d{1,2}/\d{1,2}/\d{4}", r"\d{4}-\d{2}-\d{2}",
        r"©\s*\d{4}", r"All rights reserved", r"http[s]?://\S+", r"www\.\S+",
    ]
    for p in noise:
        text = re.sub(p, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[a-zA-Z]+\b", "", text)

    nav = [r"•", r"▪", r"&", r"±±", r"——", r"\(\([^)]*\)\)", r"\b\d+\s*[a-zA-Z]+\b"]
    lines = text.split("\n")
    kept = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        special = sum(1 for c in line if c in "•●○■□▪▫▲▼◄►◆◇◈◉◊※‹›«»\"\"''±——&()[]{}")
        total = len(line.replace(" ", ""))
        if total > 0 and special / total > 0.15:
            continue
        if len(line) < 10:
            geez = sum(1 for c in line if "\u1200" <= c <= "\u137F")
            if geez < 3:
                continue
        for p in nav:
            line = re.sub(p, "", line)
        if line.strip():
            # Deduplicate characters
            line = deduplicate_geez_chars(line)
            
            # Filter by word count (at least 4 words)
            words = line.split()
            if len(words) >= 4:
                kept.append(line)

    text = "\n".join(kept)
    allowed = r"[\u1200-\u137F\u0000-\u007F\u2000-\u206F]"
    text = re.sub(f"[^{allowed}]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    return text.strip()


def extract_content_from_pdf(pdf_path: str, pdf_name: str) -> Tuple[str, int, List[Dict]]:
    """Extract and clean text and images from PDF. Returns (cleaned_text, word_count, images_info)."""
    text_content = ""
    images_info = []
    
    # Create images directory for this PDF
    images_dir = os.path.join(PDFS_DIR, 'images', pdf_name.replace('.pdf', ''))
    os.makedirs(images_dir, exist_ok=True)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text
                try:
                    t = page.extract_text()
                    if t:
                        text_content += t + "\n"
                except:
                    pass
                
                # Extract images
                try:
                    for i, image in enumerate(page.images):
                        try:
                            x0, top, x1, bottom = image['x0'], image['top'], image['x1'], image['bottom']
                            cropped_page = page.crop((x0, top, x1, bottom))
                            img_obj = cropped_page.to_image(resolution=200)
                            
                            image_filename = f"page_{page_num+1}_img_{i+1}.png"
                            image_path = os.path.join(images_dir, image_filename)
                            img_obj.save(image_path)
                            
                            images_info.append({
                                'path': image_path,
                                'page': page_num + 1,
                                'filename': image_filename
                            })
                        except:
                            pass
                except:
                    pass

            cleaned = clean_text(text_content)
            words = [w for w in cleaned.split() if w.strip()]
            return cleaned, len(words), images_info
    except Exception:
        return "", 0, []


def process_pdfs(pdf_filenames: List[str] = None) -> dict:
    """Process PDFs: extract text, perform NER, and describe images.
    
    Args:
        pdf_filenames: Optional list of specific PDF filenames to process.
                      If None, processes all PDFs in metadata.
    """
    if not os.path.exists(METADATA_PATH):
        return {"ok": False, "error": "No metadata file found. Run scraper first."}

    with open(METADATA_PATH, encoding="utf-8") as f:
        metadata = json.load(f)

    processed = []
    for item in metadata:
        fn = item.get("pdf_filename")
        if not fn:
            continue
        
        # Skip if specific filenames provided and this one isn't in the list
        if pdf_filenames is not None and fn not in pdf_filenames:
            continue
            
        path = os.path.join(PDFS_DIR, fn)
        if not os.path.exists(path):
            continue

        title = fn.split("_", 1)[1].replace(".pdf", "") if "_" in fn else fn.replace(".pdf", "")


        # Extract text and images
        text, wc, images_info = extract_content_from_pdf(path, fn)
        
        # AI Processing
        entities = ai_processor.perform_ner(text)
        
        processed_images = []
        for img in images_info:
            description = ai_processor.describe_image(img['path'])
            processed_images.append({
                'path': img['path'],
                'filename': img['filename'],
                'page': img['page'],
                'description_tigrinya': description
            })

        processed.append({
            "index": item.get("index"),
            "news_title": title,
            "article_url": item.get("article_url"),
            "publication_date": item.get("date"),
            "pdf_filename": fn,
            "pdf_url": item.get("pdf_url"),
            "extracted_text": text,
            "word_count": wc,
            "entities": entities,
            "images": processed_images,
            "processing_status": "completed",
        })

    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    total_words = sum(p["word_count"] for p in processed)
    return {
        "ok": True,
        "processed": len(processed),
        "total_words": total_words,
        "raw_data_path": RAW_DATA_PATH,
    }
