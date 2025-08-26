from fastapi import FastAPI, UploadFile, File, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from model import predict_dish_ensemble
from health_advice import get_health_verdict
from chatbot import ask_nutribot
from nutrition_combined_api import get_combined_nutrition
from cohere_helper import get_dynamic_health_context
from chatbot_prompt import get_chatbot_prompt
import uvicorn
import webbrowser
import threading
from dotenv import load_dotenv

# For the search_dish endpoint
from fastapi import Request
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI(
    title="Non-Veg Food Health API",
    description="Backend for food scanner, nutrition, chatbot",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/scan")
async def scan_food(
    file: UploadFile = File(...),
    user_quantity_g: int = Query(100, description="Quantity in grams")
):
    try:
        print(f"📸 Received file: {file.filename}")

        contents = await file.read()
        with open("temp_image.jpg", "wb") as f:
            f.write(contents)

        # 🔍 Model ensemble prediction
        dish_name, model_used, confidence, model1_info, model2_info, hf_info = predict_dish_ensemble("temp_image.jpg", {})
        print(f"🍽️ Predicted Dish: {dish_name} ({model_used}, {confidence:.2f})")

    
        print("🧠 Using Cohere for nutrition and health context...")
        # Try Cohere first
        dynamic_fields = get_dynamic_health_context(dish_name=dish_name)
        estimated_nutrition = dynamic_fields.get("estimated_nutrition", {})
        health_tags = dynamic_fields.get("health_tags", [])
        suitability = dynamic_fields.get("suitability", {})
        substitute = dynamic_fields.get("healthier_substitute", "N/A")
        source = dynamic_fields.get("source", "Cohere")

        if estimated_nutrition:
            base_nutrition = estimated_nutrition
            scale_factor = user_quantity_g / 100.0
            scaled_nutrition = {k: round(v * scale_factor, 2) for k, v in estimated_nutrition.items()}
        else:
            base_nutrition = {}
            scaled_nutrition = {}

        nutrition = {
            "per_100g": base_nutrition,
            "for_user_quantity": scaled_nutrition,
            "Health Tags": health_tags,
            "Suitability": suitability,
            "Healthier Substitute": substitute,
            "Source": source
        }

        print("✅ Nutrition and health context fetched.")
        health = get_health_verdict(dish_name, nutrition)

        # Prepare chatbot prompt for scan
        chatbot_prompt = get_chatbot_prompt(
            "scan",
            dish_name=dish_name,
            nutrition_info=str(nutrition),
            health_conditions=",".join(health.get("conditions", [])) if isinstance(health, dict) else "",
            diet_preferences=""  # Fill from user profile if available
        )
        print("🤖 Chatbot Prompt for Scan:\n", chatbot_prompt)

        # Get chatbot reply (using your ask_nutribot function)
        chatbot_reply = ask_nutribot(chatbot_prompt)

        return {
            "dish": dish_name,
            "quantity_grams": user_quantity_g,
            "model_used": model_used,
            "confidence": confidence,
            "model1_prediction": {"dish": model1_info[0], "confidence": model1_info[1]},
            "model2_prediction": {"dish": model2_info[0], "confidence": model2_info[1]},
            "huggingface_prediction": {"dish": hf_info[0], "confidence": hf_info[1]},
            "nutrition": nutrition,
            "health_verdict": health,
            "chatbot_explanation": chatbot_reply  # <-- Add this line
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

# ---------------------- Chatbot Endpoint ------------------------

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
async def chatbot_query(request: ChatRequest):
    try:
        reply = ask_nutribot(request.query)
        return {"response": reply}
    except Exception as e:
        return {"error": str(e)}

# ---------------------- Dish Search Endpoint ------------------------

@app.post("/api/search_dish")
async def search_dish(request: Request):
    try:
        data = await request.json()
        dish_name = data.get('dish_name')
        portion_size = data.get('portion_size', 100)

        print("🧠 Using Cohere for nutrition and health context...")
        # Try Cohere first
        dynamic_fields = get_dynamic_health_context(dish_name=dish_name)
        estimated_nutrition = dynamic_fields.get("estimated_nutrition", {})
        health_tags = dynamic_fields.get("health_tags", [])
        suitability = dynamic_fields.get("suitability", {})
        substitute = dynamic_fields.get("healthier_substitute", "N/A")
        source = dynamic_fields.get("source", "Cohere")

        if estimated_nutrition:
            base_nutrition = estimated_nutrition
            scale_factor = portion_size / 100.0
            scaled_nutrition = {k: round(v * scale_factor, 2) for k, v in estimated_nutrition.items()}
        else:
            base_nutrition = {}
            scaled_nutrition = {}

        result = {
            "dish": dish_name,
            "nutrition": {
                "per_100g": base_nutrition,
                "for_user_quantity": scaled_nutrition,
                "Health Tags": health_tags,
                "Suitability": suitability,
                "Healthier Substitute": substitute,
                "Source": source
            }
        }

        # Prepare chatbot prompt for search
        chatbot_prompt = get_chatbot_prompt(
            "search",
            dish_name=dish_name,
            nutrition_info=str(result["nutrition"]),
            health_conditions="",  # Fill from user profile if available
            diet_preferences=""
        )
        print("🤖 Chatbot Prompt for Search:\n", chatbot_prompt)

        # Get chatbot reply
        chatbot_reply = ask_nutribot(chatbot_prompt)

        result["chatbot_explanation"] = chatbot_reply  # Add to result

        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ---------------------- Auto-Open Swagger UI ------------------------

def open_docs():
    webbrowser.open("http://172.31.52.127:8000/docs")

if __name__ == "__main__":
    threading.Timer(1.0, open_docs).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
