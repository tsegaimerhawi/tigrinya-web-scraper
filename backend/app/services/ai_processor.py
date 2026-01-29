import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from app.config import BASE_DIR

# Load environment variables from root config.env
config_path = os.path.join(BASE_DIR, 'config.env')
load_dotenv(config_path)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try system env if not in file
    pass

if api_key:
    genai.configure(api_key=api_key)

def get_model():
    """Get the Gemini model instance."""
    if not api_key:
        return None
    try:
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Error configuring model: {e}")
        return None

def perform_ner(text):
    """
    Perform Named Entity Recognition (NER) on the given text.
    Returns a JSON object with lists of Person, Location, and Organization entities.
    """
    model = get_model()
    if not model or not text:
        return {"people": [], "locations": [], "organizations": []}

    prompt = """
    Analyze the following Tigrinya text and extract named entities.
    Return ONLY a valid JSON object with the following keys:
    - "people": list of names of people
    - "locations": list of names of places/locations
    - "organizations": list of names of organizations

    If no entities are found for a category, return an empty list.
    Do not translate the entities, keep them in Tigrinya.

    Text:
    """ + text[:30000]

    try:
        response = model.generate_content(prompt)
        # cleanup response to ensure it's valid JSON
        result_text = response.text.replace('```json', '').replace('```', '').strip()
        # Find the first { and last } to be safe
        start = result_text.find('{')
        end = result_text.rfind('}')
        if start != -1 and end != -1:
            result_text = result_text[start:end+1]
        return json.loads(result_text)
    except Exception as e:
        print(f"Error performing NER: {e}")
        return {"people": [], "locations": [], "organizations": []}

def describe_image(image_path):
    """
    Generate a description of the image in Tigrinya.
    """
    model = get_model()
    if not model or not os.path.exists(image_path):
        return ""

    try:
        # Use simpler upload if files are small or use direct bytes
        # For simplicity with generativeai SDK:
        sample_file = genai.upload_file(path=image_path, display_name="Image")
        
        prompt = "Describe this image in Tigrinya. Keep the description concise (1-2 sentences)."
        
        response = model.generate_content([sample_file, prompt])
        return response.text.strip()
    except Exception as e:
        print(f"Error describing image {image_path}: {e}")
        return ""
