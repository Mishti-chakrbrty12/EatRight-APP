import os
import cohere
from dotenv import load_dotenv
from chatbot_prompt import get_chatbot_prompt
from deepai_helper import get_deepai_completion
import concurrent.futures

# Load API key from .env
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_API_KEY)

def ask_nutribot(question: str) -> str:
    try:
        response = co.chat(
            model="command-r-plus",
            message=question,
            temperature=0.6
        )
        return response.text
    except Exception as e:
        print(f"❌ Cohere error: {e}")
        # Fallback to DeepAI
        deepai_output = get_deepai_completion(question)
        return deepai_output or "Sorry, I couldn't generate a response at this time."

def get_dynamic_health_context(nutrition: dict) -> dict:
    nutrition_lines = "\n".join([f"{k}: {v}" for k, v in nutrition.items()])
    
    prompt = f"""
Given the following nutrition values for a food item, generate:

1. Health Tags (like "High Protein", "Low Carb", etc.)
2. Suitability for these conditions:
   - diabetes
   - heart disease
   - high BP
   - low BP
   - high cholesterol
   - kidney disease
3. A healthier substitute suggestion.

Nutrition Data:
{nutrition_lines}
    """

    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt.strip(),
            temperature=0.3,
            max_tokens=300
        )

        text = response.generations[0].text.strip()
        print("Cohere Response:\n", text)

        # OPTIONAL: parse the response using regex or eval if it's JSON-style
        return text
    except Exception as e:
        print(f"Cohere API error: {e}")
        return {}

