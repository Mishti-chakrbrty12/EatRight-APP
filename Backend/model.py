import torch
from PIL import Image
from transformers import ViTImageProcessor, ViTForImageClassification 
from torchvision.models import resnet18
import json
from torchvision import transforms
import torch.nn.functional as F
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Set paths
MODEL_PATH_1 = "C:/Users/HP/Downloads/archive (4)/vit-food-final"
MODEL_PATH_2 = "C:/Users/HP/Downloads/archive (4)/food_classifier_final.pth"
LABEL_MAP_PATH = "C:/Users/HP/Downloads/all_non_veg_dishes_health_info.json"

# Load model and processor
model1 = ViTForImageClassification.from_pretrained(MODEL_PATH_1) # ViT model
processor = ViTImageProcessor.from_pretrained(MODEL_PATH_1) # ViT processor for image preprocessing (resizing, normalizing, etc.)                               

# Load ResNet-18 model for 67 classes
model2 = resnet18(pretrained=False)
model2.fc = torch.nn.Linear(model2.fc.in_features, 67)  # or len(class_names) if you want to dynamically set it
model2.load_state_dict(torch.load(MODEL_PATH_2))
model2.eval()
# You will need to handle preprocessing manually (not with HuggingFace processor)

# Load label map
with open(LABEL_MAP_PATH, "r") as f:
    raw_map = json.load(f)
    # Handle both dict and list formats
    if isinstance(raw_map, list):
        dish_names = [item["dish"] for item in raw_map]
    else:
        dish_names = [item["dish"] for item in raw_map.values()]

# Set id2label and label2id in model config
id2label = {i: name for i, name in enumerate(dish_names)}
label2id = {name: i for i, name in id2label.items()}
model1.config.id2label = id2label
model1.config.label2id = label2id

# Preprocessing for ResNet-18
preprocess_resnet = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

def predict_with_huggingface(image_path: str):
    """
    Predicts a dish using a Hugging Face Inference API food classification model.
    Returns (label, confidence) or ("HF unavailable", 0.0) on error.
    """
    if not HF_API_TOKEN:
        print("HF_API_TOKEN not found in .env file. Skipping Hugging Face prediction.")
        return "HF unavailable", 0.0
    
    api_url = "https://api-inference.huggingface.co/models/nateraw/food"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        response = requests.post(api_url, headers=headers, data=image_bytes)
        if response.status_code != 200:
            print(f"Hugging Face API error: {response.status_code} {response.text}")
            return "HF API error", 0.0
        result = response.json()
        if isinstance(result, dict) and result.get("error"):
            print(f"Hugging Face API error: {result['error']}")
            return "HF API error", 0.0
        # result is a list of predictions
        top = result[0]
        label = top["label"]
        score = top["score"]
        print(f"Hugging Face Prediction: {label} (confidence={score:.3f})")
        return label, score
    except Exception as e:
        print("Error calling Hugging Face API:", repr(e))
        return "HF API error", 0.0

def predict_dish(image_path: str):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model1(**inputs)
    logits = outputs.logits
    probs = F.softmax(logits, dim=1)
    predicted_class_idx = logits.argmax(-1).item()
    confidence = probs[0, predicted_class_idx].item()
    label = model1.config.id2label[predicted_class_idx]
    cleaned_label = label.replace("_", " ")
    return cleaned_label, confidence

def predict_dish_model2(image_path: str):
    image = Image.open(image_path).convert("RGB")
    input_tensor = preprocess_resnet(image).unsqueeze(0)
    with torch.no_grad():
        outputs = model2(input_tensor)
    probs = F.softmax(outputs, dim=1)
    predicted_class_idx = outputs.argmax(-1).item()
    confidence = probs[0, predicted_class_idx].item()
    label = id2label[predicted_class_idx]
    cleaned_label = label.replace("_", " ")
    return cleaned_label, confidence

# Ensemble prediction: try model1, fallback to model2 if not found in nutrition data

def predict_dish_ensemble(image_path: str, nutrition_data=None):
    label1, conf1 = predict_dish(image_path)
    label2, conf2 = predict_dish_model2(image_path)
    hf_label, hf_conf = predict_with_huggingface(image_path)

    # Choose the best prediction among all three
    if hf_conf > max(conf1, conf2):
        best_label, model_used, confidence = hf_label, "huggingface", hf_conf
    elif conf1 >= conf2:
        best_label, model_used, confidence = label1, 'model1', conf1
    else:
        best_label, model_used, confidence = label2, 'model2', conf2

    return best_label, model_used, confidence, (label1, conf1), (label2, conf2), (hf_label, hf_conf)
