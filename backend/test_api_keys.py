import os
import requests
from dotenv import load_dotenv

# Inside the docker container, environment variables are already loaded, 
# but we do load_dotenv just in case it's run locally.
load_dotenv("../.env")

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return "FAIL (Key not found in environment)"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
        res = requests.post(url, json={"contents":[{"parts":[{"text":"Hi"}]}]}, headers={"Content-Type": "application/json"})
        if res.status_code == 200:
            return "SUCCESS ✅"
        return f"FAIL ❌ ({res.status_code}: {res.json().get('error', {}).get('message', res.text)})"
    except Exception as e:
        return f"ERROR ❌ ({e})"

def test_factcheck():
    api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY")
    if not api_key: return "FAIL (Key not found in environment)"
    try:
        url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query=earth&key={api_key}"
        res = requests.get(url)
        if res.status_code == 200:
            return "SUCCESS ✅"
        return f"FAIL ❌ ({res.status_code}: {res.json().get('error', {}).get('message', res.text)})"
    except Exception as e:
        return f"ERROR ❌ ({e})"

def test_gnews():
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key: return "FAIL (Key not found in environment)"
    try:
        url = f"https://gnews.io/api/v4/search?q=technology&max=1&apikey={api_key}"
        res = requests.get(url)
        if res.status_code == 200:
            return "SUCCESS ✅"
        err_msg = res.json().get("errors", res.json().get("message", res.text))
        return f"FAIL ❌ ({res.status_code}: {err_msg})"
    except Exception as e:
        return f"ERROR ❌ ({e})"

if __name__ == "__main__":
    print("-" * 50)
    print("TruthLens API Keys Diagnostic Test")
    print("-" * 50)
    print(f"Gemini API:           {test_gemini()}")
    print(f"Google FactCheck API: {test_factcheck()}")
    print(f"GNews API:            {test_gnews()}")
    print("-" * 50)
