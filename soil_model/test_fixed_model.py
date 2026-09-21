import tensorflow as tf
import json
from PIL import Image
import numpy as np

MODEL_PATH = "soil_classifier_fixed.keras"
CLASS_PATH = "class_names_fixed.json"

model = tf.keras.models.load_model(MODEL_PATH)

with open(CLASS_PATH, "r") as f:
    classes = json.load(f)

print("=" * 60)
print("FIXED SOIL MODEL TEST")
print("=" * 60)

print("\nClasses:")
for i, name in enumerate(classes):
    print(f"{i}: {name}")

for filename in ["soil1.png", "soil2.png"]:
    image_path = "test_images/" + filename

    image = Image.open(image_path).convert("RGB")
    image = image.resize((224, 224))

    image_array = np.array(image, dtype=np.float32) / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    predictions = model.predict(image_array, verbose=0)[0]

    predicted_index = int(np.argmax(predictions))
    predicted_class = classes[predicted_index]
    confidence = float(predictions[predicted_index]) * 100

    print("\n" + "-" * 60)
    print(f"Image      : {filename}")
    print(f"Prediction : {predicted_class}")
    print(f"Confidence : {confidence:.2f}%")

    print("\nAll predictions:")
    for i, score in enumerate(predictions):
        print(f"  {classes[i]:20s} {score * 100:.2f}%")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)