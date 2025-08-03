from fastapi import FastAPI, UploadFile, File
from model import predict_dish_ensemble
from health_advice import get_health_verdict
from chatbot import ask_nutribot
import json
import webbrowser
import threading
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Non-Veg Food Health API",
    description="Backend for food scanner, nutrition, chatbot",
    version="1.0"
)

# Add CORS Middleware to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://localhost:5000"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load nutrition data
with open("C:/Users/HP/Downloads/all_non_veg_dishes_health_info.json", "r") as f:
    raw_data = json.load(f)
    nutrition_data = {
        item["dish"].lower(): {
            "Calories": item["nutrition"].get("calories_kcal", "N/A"),
            "Protein": item["nutrition"].get("protein_g", "N/A"),
            "Fats": item["nutrition"].get("fat_g", "N/A"),
            "Carbs": item["nutrition"].get("carbs_g", "N/A"),
            "Health Benefits": item.get("health_benefits", []),
            "Suitability": item.get("suitability", {}),
            "Healthier Substitute": item.get("healthier_substitute", "N/A")
        }
        for item in raw_data
    }

# ✅ /scan endpoint
@app.post("/scan")
async def scan_food(file: UploadFile = File(...)):
    try:
        print(f"\U0001F4F8 Received file: {file.filename}")

        # Save uploaded image
        contents = await file.read()
        with open("temp_image.jpg", "wb") as f:
            f.write(contents)
        print("\u2705 Saved uploaded image as temp_image.jpg")

        # Predict dish name using ensemble (returns best, model used, confidence, and all models' info)
        dish_name, model_used, confidence, model1_info, model2_info, hf_info = predict_dish_ensemble("temp_image.jpg", nutrition_data)
        print(f"\U0001F37D\uFE0F Predicted Dish: {dish_name} (from {model_used}, confidence={confidence:.3f})")
        print(f"Model 1: {model1_info[0]} (conf={model1_info[1]:.3f}) | Model 2: {model2_info[0]} (conf={model2_info[1]:.3f}) | HuggingFace: {hf_info[0]} (conf={hf_info[1]:.3f})")
        print(f"Lowercase: '{dish_name.lower()}'")
        print(f"Available nutrition keys: {list(nutrition_data.keys())[:10]} ...")  # print first 10 keys

        # Check if the key exists
        if dish_name.lower() in nutrition_data:
            print("Dish found in nutrition data!")
        else:
            print("Dish NOT found in nutrition data!")

        # Get nutrition info
        nutrition = nutrition_data.get(dish_name.lower(), {
            "Calories": "N/A",
            "Protein": "N/A",
            "Fats": "N/A",
            "Carbs": "N/A",
            "Health Benefits": [],
            "Suitability": {},
            "Healthier Substitute": "N/A"
        })
        print(f"\U0001F4CA Nutrition: {nutrition}")

        # Get health verdict
        if "N/A" in nutrition.values():
            health = "No health verdict available due to missing nutrition data."
        else:
            health = get_health_verdict(dish_name, nutrition)

        return {
            "dish": dish_name,
            "model_used": model_used,
            "confidence": confidence,
            "model1_prediction": {"dish": model1_info[0], "confidence": model1_info[1]},
            "model2_prediction": {"dish": model2_info[0], "confidence": model2_info[1]},
            "huggingface_prediction": {"dish": hf_info[0], "confidence": hf_info[1]},
            "nutrition": nutrition,
            "health_verdict": health
        }

    except Exception as e:
        print(f"\u274c Error: {e}")
        return {"error": str(e)}

# ✅ /chat endpoint
class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
async def chatbot_query(request: ChatRequest):
    try:
        reply = ask_nutribot(request.query)
        return {"response": reply}
    except Exception as e:
        return {"error": str(e)}

# ✅ Auto-open Swagger UI
def open_docs():
    webbrowser.open("http://127.0.0.1:8000/docs")

# ✅ Run the app
if __name__ == "__main__":
    threading.Timer(1.0, open_docs).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
