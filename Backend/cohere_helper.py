import os
import cohere
import json
import re
import concurrent.futures
from dotenv import load_dotenv
from deepai_helper import get_deepai_completion
load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY)

def get_dynamic_health_context(nutrition_data: dict = None, dish_name: str = None, timeout=15):
    try:
        if nutrition_data and len(nutrition_data) > 0:
            # Remove None values and convert to floats
            safe_nutrition_data = {k: float(v) for k, v in nutrition_data.items() if v is not None}
            prompt = f"""
You are a health-focused nutrition expert. Given the nutrition data of a non-vegetarian dish per 100g, analyze and return the following fields in proper JSON:

1. "health_tags": A list of 3–6 tags such as "high protein", "low fat", "iron-rich", etc.
2. "suitability": A dictionary with health conditions as keys (heart_disease, high_BP, low_BP, diabetes, high_cholesterol, kidney) and 1-line advice.
3. "healthier_substitute": One practical suggestion to make the dish healthier.

Here is the nutrition data:
{json.dumps(safe_nutrition_data, indent=2)}

Respond only in JSON.
"""
        elif dish_name:
            prompt = f"""
You are a health-focused nutrition expert. Given the name of a non-vegetarian dish, estimate its typical nutrition profile and return the following fields in proper JSON:

1. "health_tags": A list of 3–6 tags such as "high protein", "low fat", "iron-rich", etc.
2. "suitability": A dictionary with health conditions as keys (heart_disease, high_BP, low_BP, diabetes, high_cholesterol, kidney) and 1-line advice.
3. "healthier_substitute": One practical suggestion to make the dish healthier.
4. "estimated_nutrition": A dictionary with estimated values for calories, protein, fat, carbs, fiber, iron, sodium, cholesterol, etc. (per 100g).

Dish name: "{dish_name}"

Respond only in JSON.
"""
        else:
            raise ValueError("Either nutrition_data or dish_name must be provided.")

        response = call_cohere_api(prompt)
        
        text = response.generations[0].text.strip()
        print("🤖 Cohere Response:")
        print(text)

        # Remove code block markers if present
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()

        # Remove stray backslashes
        text = text.replace("\\", "")

        # Remove units from both integers and floats (e.g., 1.5mg, 25g)
        text = re.sub(r'(\d+(\.\d+)?)\s*(g|mg|kcal|mcg)', r'\1', text)

        # Remove trailing commas before closing braces/brackets
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        # Fix "healthier_substitute" if it's an object
        try:
            data = json.loads(text)
            substitute = data.get("healthier_substitute")
            if isinstance(substitute, dict):
                substitute = substitute.get("suggestion", "N/A")
            elif not isinstance(substitute, str):
                substitute = "N/A"
            data["healthier_substitute"] = substitute
            text = json.dumps(data)
        except Exception as e:
            print("JSON post-processing error:", e)

        return json.loads(text)

    except Exception as e:
        print(f"❌ Cohere error: {e}")
        # Fallback to DeepAI
        deepai_output = get_deepai_completion(prompt)
        try:
            data = json.loads(deepai_output)
            return {
                "estimated_nutrition": data.get("estimated_nutrition", {}),
                "health_tags": data.get("health_tags", []),
                "suitability": data.get("suitability", {}),
                "healthier_substitute": data.get("healthier_substitute", "N/A"),
                "source": "DeepAI",
                "raw_output": deepai_output
            }
        except Exception:
            # fallback to your current structure
            return {
                "estimated_nutrition": {},  # Parse from deepai_output if possible
                "health_tags": [],
                "suitability": {},
                "healthier_substitute": "N/A",
                "source": "DeepAI",
                "raw_output": deepai_output
            }

def call_cohere_api(prompt):
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        temperature=0.4,
        max_tokens=350
    )
    return response
