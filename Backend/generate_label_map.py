import os
import json
from torchvision.datasets import ImageFolder

# Path to your training dataset (same used for model training)
dataset_path = "C:/Users/HP/Downloads/archive (4)/images" # adjust this if needed

# Load dataset to get class-to-index mapping
dataset = ImageFolder(dataset_path)
idx_to_class = {v: k for k, v in dataset.class_to_idx.items()}

# Convert index-label map to string keys (e.g., {"0": "Butter Chicken"})
label_map = {i: name for i, name in idx_to_class.items()}

# Save to label_map.json
with open("label_map.json", "w") as f:
    json.dump(label_map, f, indent=4)

print("✅ label_map.json generated successfully.")
