import tensorflow as tf
import numpy as np
import json
from PIL import Image
from pathlib import Path

MODEL_PATH = "soil_classifier.keras"
DATASET_DIR = Path("CyAUG-Dataset")

model = tf.keras.models.load_model(MODEL_PATH)

with open("class_names.json", "r") as f:
    class_names = json.load(f)

print("\nMODEL DIAGNOSTIC")
print("=" * 70)

for class_dir in sorted(DATASET_DIR.iterdir()):
    if not class_dir.is_dir():
        continue

    images = [
        p for p in class_dir.iterdir()
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
        and p.stat().st_size > 0
    ]

    if not images:
        continue

    # Test first image from this class
    image_path = images[0]

    image = (
        Image.open(image_path)
        .convert("RGB")
        .resize((224, 224))
    )

    x = np.asarray(image, dtype=np.float32) / 255.0
    x = np.expand_dims(x, axis=0)

    prediction = model.predict(x, verbose=0)[0]

    index = int(np.argmax(prediction))
    confidence = float(prediction[index]) * 100

    print(
        f"{class_dir.name:18} -> "
        f"{class_names[index]:18} "
        f"{confidence:.2f}%"
    )