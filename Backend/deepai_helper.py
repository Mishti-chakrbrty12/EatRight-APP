from dotenv import load_dotenv
import os
import requests

load_dotenv()
DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")

def get_deepai_completion(prompt, timeout=15):
    url = "https://api.deepai.org/api/text-generator"
    headers = {"api-key": DEEPAI_API_KEY}
    try:
        response = requests.post(url, data={'text': prompt}, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("output", "")
    except Exception as e:
        print(f"DeepAI error: {e}")
        return ""