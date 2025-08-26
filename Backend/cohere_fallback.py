import cohere
import os
from dotenv import load_dotenv

load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))  # add your key to .env

def get_dynamic_health_context(nutrients: dict):
    try:
        prompt = (
            f"Given the following nutrition content per portion:\n"
            f"{nutrients}\n\n"
            "Return JSON with 3 fields:\n"
            "1. 'Health Tags' (like high_protein, low_fat etc),\n"
            "2. 'Suitability' (dictionary with disease names like diabetes, heart_disease as keys and 1-line suitability text as values),\n"
            "3. 'Healthier Substitute' (one suggestion to make the dish healthier).\n"
            "Respond in JSON only."
        )

        response = co.generate(
            model="command-r",
            prompt=prompt,
            max_tokens=300,
            temperature=0.5,
        )

        text = response.generations[0].text.strip()
        print("🤖 Cohere Fallback Output:", text)

        # Convert stringified JSON to Python dict
        import json
        return json.loads(text)

    except Exception as e:
        print("❌ Cohere fallback error:", e)
        return {
            "Health Tags": [],
            "Suitability": {},
            "Healthier Substitute": "N/A"
        }
