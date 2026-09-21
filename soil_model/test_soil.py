import json
import numpy as np
import tensorflow as tf
from PIL import Image
from pathlib import Path

MODEL_PATH = "soil_classifier.keras"
CLASS_PATH = "class_names.json"
TEST_DIR = Path("test_images")

model = tf.keras.models.load_model(MODEL_PATH)

with open(CLASS_PATH, "r") as f:
    class_names = json.load(f)

print("\n🌱 SOIL MODEL TEST\n")

for image_path in TEST_DIR.iterdir():

    if image_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
        continue

    image = Image.open(image_path).convert("RGB")
    image = image.resize((224, 224))

    img_array = np.array(image, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array, verbose=0)[0]

    predicted_index = np.argmax(predictions)
    predicted_class = class_names[predicted_index]
    confidence = predictions[predicted_index] * 100

    print(f"📷 {image_path.name}")
    print(f"   Prediction: {predicted_class}")
    print(f"   Confidence: {confidence:.2f}%")
    print()