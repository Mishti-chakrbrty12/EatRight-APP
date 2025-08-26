# nutrition_combined_api.py (UPDATED WITH MERGING & DYNAMIC)
import requests
import os

# Replace with real keys or use dotenv in deployment
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY") or "3f63514bf7c645e88a0a765185923a7a"
EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID") or "99d15386"
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY") or "5e8830401ac33e7007404cdf6925d81e"
USDA_API_KEY = os.getenv("USDA_API_KEY") or "y5rLgZZKvuZ4SviTMIuZzXzGLGvRDiqzzrl9WZTT"

def try_spoonacular(dish_name):
    try:
        url = f"https://api.spoonacular.com/recipes/guessNutrition?title={dish_name}&apiKey={SPOONACULAR_API_KEY}"
        res = requests.get(url)
        data = res.json()
        if res.status_code == 200 and data:
            return {
                "Calories": round(data["calories"]["value"], 2),
                "Protein": round(data["protein"]["value"], 2),
                "Fats": round(data["fat"]["value"], 2),
                "Carbs": round(data["carbs"]["value"], 2),
                "source": "Spoonacular"
            }
    except:
        pass
    return None

def try_edamam(dish_name):
    try:
        url = "https://api.edamam.com/api/nutrition-data"
        params = {
            "app_id": EDAMAM_APP_ID,
            "app_key": EDAMAM_APP_KEY,
            "ingr": dish_name
        }
        res = requests.get(url, params=params)
        data = res.json()
        if res.status_code == 200 and data.get("calories", 0) > 0:
            sugar = data["totalNutrients"].get("SUGAR", {}).get("quantity", 0)
            sodium = data["totalNutrients"].get("NA", {}).get("quantity", 0)
            fat = data["totalNutrients"].get("FAT", {}).get("quantity", 0)
            protein = data["totalNutrients"].get("PROCNT", {}).get("quantity", 0)
            carbs = data["totalNutrients"].get("CHOCDF", {}).get("quantity", 0)

            suitability = {
                "diabetes": "avoid" if sugar > 15 or carbs > 50 else "acceptable",
                "high_BP": "not recommended" if sodium > 800 else "acceptable",
                "heart_disease": "caution" if fat > 30 else "acceptable",
                "high_cholesterol": "not recommended" if fat > 25 else "acceptable",
                "low_BP": "acceptable",
                "kidney": "caution"
            }

            nutrients = {
                "Calories": data.get("calories", 0),
                "Protein": protein,
                "Fats": fat,
                "Carbs": carbs,
                "Iron": data["totalNutrients"].get("FE", {}).get("quantity", 0),
                "Calcium": data["totalNutrients"].get("CA", {}).get("quantity", 0),
                "Fiber": data["totalNutrients"].get("FIBTG", {}).get("quantity", 0),
                "Sugar": sugar,
                "Cholesterol": data["totalNutrients"].get("CHOLE", {}).get("quantity", 0),
                "Sodium": sodium
            }

            return {
                "full_nutrients": nutrients,
                "health_tags": data.get("healthLabels", []),
                "suitability": suitability,
                "healthier_substitute": "Use less oil/salt and prefer grilled version",
                "source": "Edamam"
            }
    except:
        pass
    return None

def try_usda(dish_name):
    try:
        search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "api_key": USDA_API_KEY,
            "query": dish_name,
            "pageSize": 1
        }
        res = requests.get(search_url, params=params)
        results = res.json().get("foods", [])
        if results:
            fdc_id = results[0]["fdcId"]
            details_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={USDA_API_KEY}"
            res2 = requests.get(details_url)
            nutrients = {n["nutrientName"]: n["value"] for n in res2.json().get("foodNutrients", [])}
            return {
                "Calories": nutrients.get("Energy", 0),
                "Protein": nutrients.get("Protein", 0),
                "Fats": nutrients.get("Total lipid (fat)", 0),
                "Carbs": nutrients.get("Carbohydrate, by difference", 0),
                "Iron": nutrients.get("Iron, Fe", 0),
                "Calcium": nutrients.get("Calcium, Ca", 0),
                "Fiber": nutrients.get("Fiber, total dietary", 0),
                "Sugar": nutrients.get("Sugars, total including NLEA", 0),
                "Cholesterol": nutrients.get("Cholesterol", 0),
                "Sodium": nutrients.get("Sodium, Na", 0),
                "source": "USDA"
            }
    except:
        pass
    return None

def get_combined_nutrition(dish_name=None, barcode=None):
    result = {
        "dish": dish_name,
        "quantity_consumed_g": None,
        "model_used": None,
        "confidence": None,
        "model1_prediction": None,
        "model2_prediction": None,
        "huggingface_prediction": None,
        "nutrition": None,
        "health_verdict": None,
    }

    # First try Edamam for full data
    if dish_name:
        edamam = try_edamam(dish_name)
        if edamam:
            result["nutrition"] = {
                "per_100g": edamam.get("full_nutrients", {}),
            }
            result["health_verdict"] = {
                "suitability": edamam.get("suitability", {}),
                "health_tags": edamam.get("health_tags", []),
                "healthier_substitute": edamam.get("healthier_substitute", "N/A")
            }
            result["model_used"] = "edamam"
            return result

    # Else try Spoonacular and enhance if possible
    if dish_name:
        spoon = try_spoonacular(dish_name)
        if spoon:
            return {
                "full_nutrients": {k: v for k, v in spoon.items() if k != "source"},
                "health_tags": [],
                "suitability": {},
                "healthier_substitute": "N/A",
                "source": "Spoonacular"
            }

    # Finally USDA if others fail
    search_term = barcode or dish_name
    if search_term:
        usda = try_usda(search_term)
        if usda:
            result["nutrition"] = {
                "per_100g": {k: v for k, v in usda.items() if k != "source"},
            }
            result["model_used"] = "usda"
            return result

    result["error"] = "No nutrition found from APIs"
    return result

if __name__ == "__main__":
    import json
    result = get_combined_nutrition(dish_name="Butter Chicken")
    print(json.dumps(result, indent=2))
