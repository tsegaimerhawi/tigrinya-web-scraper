"""App configuration and newspaper definitions."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.environ.get("TIGRINYA_DATA_DIR", BASE_DIR)
PDFS_DIR = os.path.join(DATA_DIR, "pdfs")
METADATA_PATH = os.path.join(DATA_DIR, "pdf_metadata.json")
RAW_DATA_PATH = os.path.join(DATA_DIR, "raw_data.json")

NEWSPAPERS = [
    {
        "id": "haddas-ertra",
        "name": "Haddas Ertra",
        "source": "shabait.com",
        "base_url": "https://shabait.com/category/newspapers/haddas-ertra-news",
        "link_selector_href": "haddas-ertra",
        "description": "Tigrinya newspaper from Eritrea Ministry of Information",
    },
]

NEWSPAPERS_BY_ID = {n["id"]: n for n in NEWSPAPERS}
