import os
import sys
import json
import re
import pdfplumber

# Add backend to path to reuse ai_processor
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.services import ai_processor

def clean_text(text):
    """Clean extracted text by keeping only Ge'ez script characters, numbers, and punctuation."""
    if not text:
        return ""

    # Remove common newspaper noise patterns
    noise_patterns = [
        r'PAGE\s+\d+', r'page\s+\d+', r'waga\s+[\d.]+', r'ዋጋ\s+[\d.]+',
        r'ISSUE\s+\d+', r'VOL\s+\d+', r'VOLUME\s+\d+',
        r'\d{1,2}/\d{1,2}/\d{4}', r'\d{4}-\d{2}-\d{2}',
        r'©\s*\d{4}', r'All rights reserved', r'http[s]?://\S+', r'www\.\S+'
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove English words
    text = re.sub(r'\b[a-zA-Z]+\b', '', text)

    # Remove navigation elements
    navigation_patterns = [
        r'•', r'', r'&', r'±±', r'——', r'\(\([^)]*\)\)', r'\b\d+\s*[a-zA-Z]+\b'
    ]

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip lines with too many special characters
        special_count = sum(1 for c in line if c in '•●○■□▪▫▲▼◄►◆◇◈◉◊※‹›«»""''±——&()[]{}')
        total_chars = len(line.replace(' ', ''))
        if total_chars > 0 and special_count / total_chars > 0.15:
            continue

        # Skip very short lines
        if len(line) < 10:
            geez_chars = sum(1 for c in line if '\u1200' <= c <= '\u137F')
            if geez_chars < 3:
                continue

        # Remove navigation patterns
        for pattern in navigation_patterns:
            line = re.sub(pattern, '', line)

        if line.strip():
            cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # Keep only Ge'ez script, numbers, and punctuation
    allowed_chars = r'[\u1200-\u137F\u0000-\u007F\u2000-\u206F]'
    text = re.sub(f'[^{allowed_chars}]', '', text)

    # Clean whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()


def extract_content_from_pdf(pdf_path, pdf_name):
    """Extract text and images from PDF using pdfplumber."""
    text_content = ""
    images_info = []
    
    # Create images directory for this PDF
    images_dir = os.path.join(os.path.dirname(pdf_path), 'images', pdf_name.replace('.pdf', ''))
    os.makedirs(images_dir, exist_ok=True)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                except:
                    pass
                
                # Extract images
                try:
                    for i, image in enumerate(page.images):
                        try:
                            # Get image object
                            x0, top, x1, bottom = image['x0'], image['top'], image['x1'], image['bottom']
                            cropped_page = page.crop((x0, top, x1, bottom))
                            img_obj = cropped_page.to_image(resolution=200)
                            
                            # Save image
                            image_filename = f"page_{page_num+1}_img_{i+1}.png"
                            image_path = os.path.join(images_dir, image_filename)
                            img_obj.save(image_path)
                            
                            images_info.append({
                                'path': image_path,
                                'page': page_num + 1,
                                'filename': image_filename
                            })
                        except Exception as img_err:
                            print(f"Error extracting image {i} on page {page_num}: {img_err}")
                except Exception as e:
                    print(f"Error processing images on page {page_num}: {e}")

            cleaned_text = clean_text(text_content)
            words = [word for word in cleaned_text.split() if word.strip()]
            
            return cleaned_text, len(words), images_info
            
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return "", 0, []


def process_pdfs():
    """Process all PDFs and create structured JSON output."""
    with open('pdf_metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    completed_metadata = [item for item in metadata if item.get('download_status') == 'completed']

    if not completed_metadata:
        print("No completed PDF downloads found")
        return

    processed_data = []

    print(f"Processing {len(completed_metadata)} PDFs...")

    for i, item in enumerate(completed_metadata):
        pdf_path = item.get('pdf_filepath')
        if not pdf_path or not os.path.exists(pdf_path):
            continue
            
        print(f"Processing {i+1}/{len(completed_metadata)}: {item.get('pdf_filename')}")

        # Extract news title from filename
        filename = item.get('pdf_filename', '')
        news_title = filename.split('_', 1)[1].replace('.pdf', '') if '_' in filename else filename.replace('.pdf', '')

        # Extract text and images
        extracted_text, word_count, images_info = extract_content_from_pdf(pdf_path, filename)
        
        # Perform AI tasks
        print("  - Performing NER...")
        entities = ai_processor.perform_ner(extracted_text)
        
        processed_images = []
        api_key_error_logged = {}
        if images_info:
            print(f"  - Describing {len(images_info)} images...")
            for img in images_info:
                description = ai_processor.describe_image(img['path'], _api_key_error_logged=api_key_error_logged)
                processed_images.append({
                    'path': img['path'],
                    'filename': img['filename'],
                    'page': img['page'],
                    'description_tigrinya': description
                })

        processed_entry = {
            'index': item.get('index'),
            'news_title': news_title,
            'article_url': item.get('article_url'),
            'publication_date': item.get('date'),
            'pdf_filename': item.get('pdf_filename'),
            'pdf_url': item.get('pdf_url'),
            'extracted_text': extracted_text,
            'word_count': word_count,
            'entities': entities,
            'images': processed_images,
            'processing_status': 'completed'
        }

        processed_data.append(processed_entry)

    # Save processed data
    with open('raw_data.json', 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

    # Summary
    total_words = sum(item['word_count'] for item in processed_data)
    print(f"\nProcessing Complete!")
    print(f"Processed {len(processed_data)} PDFs")
    print(f"Total words extracted: {total_words}")
    print(f"Average words per PDF: {total_words/len(processed_data):.1f}")
    print("All text has been cleaned to contain only Ge'ez script characters.")
    print("Entities extracted and images described in Tigrinya.")


if __name__ == "__main__":
    process_pdfs()
