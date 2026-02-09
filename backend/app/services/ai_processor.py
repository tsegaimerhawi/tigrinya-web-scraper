import os
import json
import warnings
from dotenv import load_dotenv
from app.config import BASE_DIR

# Load config.env but do not override existing env (so GOOGLE_API_KEY from shell is kept)
config_path = os.path.join(BASE_DIR, 'config.env')
load_dotenv(config_path, override=False)

# Use deprecated package with suppressed FutureWarning; model name updated for current API
with warnings.catch_warnings(action="ignore", category=FutureWarning):
    import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Model supported by current Gemini API (gemini-1.5-flash often returns 404 on v1beta)
GEMINI_MODEL = "gemini-2.0-flash"


def get_model():
    """Get the Gemini model instance."""
    if not api_key:
        return None
    try:
        return genai.GenerativeModel(GEMINI_MODEL)
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
        err_str = str(e)
        if "API key" in err_str and ("expired" in err_str or "invalid" in err_str.lower() or "API_KEY_INVALID" in err_str):
            print("Error performing NER: API key expired or invalid. Set GOOGLE_API_KEY in your shell (e.g. in ~/.zshrc) or put a valid key in config.env.")
        else:
            print(f"Error performing NER: {e}")
        return {"people": [], "locations": [], "organizations": []}

def _is_api_key_error(e: Exception) -> bool:
    err = str(e)
    return (
        "API key" in err
        and ("expired" in err or "invalid" in err.lower() or "API_KEY_INVALID" in err)
    )


def describe_image(image_path, _api_key_error_logged=None):
    """
    Generate a description of the image in Tigrinya.
    Uses _api_key_error_logged (mutable container) to log API key errors only once.
    """
    model = get_model()
    if not model or not os.path.exists(image_path):
        return ""

    try:
        sample_file = genai.upload_file(path=image_path, display_name="Image")
        prompt = "Describe this image in Tigrinya. Keep the description concise (1-2 sentences)."
        response = model.generate_content([sample_file, prompt])
        return response.text.strip()
    except Exception as e:
        if _is_api_key_error(e):
            if _api_key_error_logged is not None and not _api_key_error_logged.get("done"):
                _api_key_error_logged["done"] = True
                print(
                    "Error describing images: API key expired or invalid. "
                    "Set GOOGLE_API_KEY in your shell (e.g. in ~/.zshrc) or put a valid key in config.env."
                )
        else:
            print(f"Error describing image {image_path}: {e}")
        return ""
