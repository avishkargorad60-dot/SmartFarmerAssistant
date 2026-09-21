
import json
import os

# Heavy ML/image libs are imported lazily inside functions to avoid import
# errors when this module is imported in test environments that don't have
# onnxruntime / numpy / Pillow installed.

# Make model and class paths explicit and relative to this file so the
# module can be imported from other locations without path errors.
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model.onnx")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "class_names.json")


def load_model():
    """Load the ONNX disease classification model."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Disease model file not found: {MODEL_PATH}")

    if os.path.getsize(MODEL_PATH) == 0:
        raise ValueError(f"Disease model file is empty: {MODEL_PATH}. Provide a valid ONNX export.")

    import onnxruntime as ort
    session = ort.InferenceSession(
        MODEL_PATH,
        providers=["CPUExecutionProvider"]
    )
    return session


def load_class_names():
    """Load disease names from JSON file."""
    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def preprocess_image(image_path):
    """Prepare image for the model."""
    from PIL import Image
    import numpy as np

    image = Image.open(image_path).convert("RGB")

    # Model expects 224 x 224 image
    image = image.resize((224, 224))

    image = np.array(image).astype(np.float32) / 255.0

    # ImageNet normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    image = (image - mean) / std

    # HWC -> CHW
    image = np.transpose(image, (2, 0, 1))

    # Add batch dimension
    image = np.expand_dims(image, axis=0)

    return image.astype(np.float32)


def predict_disease(image_path):
    """Predict possible crop disease from an image."""
    # Defer heavy imports until prediction time
    import numpy as np

    session = load_model()
    class_names = load_class_names()

    image = preprocess_image(image_path)

    input_name = session.get_inputs()[0].name

    output = session.run(None, {input_name: image})

    predictions = output[0][0]

    # Convert logits to probabilities
    exp_predictions = np.exp(predictions - np.max(predictions))
    probabilities = exp_predictions / exp_predictions.sum()

    predicted_index = int(np.argmax(probabilities))
    confidence = float(probabilities[predicted_index] * 100)

    disease = class_names[predicted_index]

    return disease, confidence


if __name__ == "__main__":

    print("\n🐛 SMART FARMER - CROP DISEASE AGENT")
    print("--------------------------------------")

    image_path = input(
        "Enter image path: "
    ).strip()

    try:

        disease, confidence = predict_disease(
            image_path
        )

        print("\n🌱 ANALYSIS RESULT")
        print("----------------------")

        print("Possible Disease:", disease)

        print(
            "Confidence:",
            f"{confidence:.2f}%"
        )

        print(
            "\n⚠️ This is an AI-based screening result. "
            "It should not be treated as a confirmed "
            "agricultural diagnosis."
        )

    except FileNotFoundError:
        print("\n❌ Image or model file not found.")

    except Exception as error:
        print("\n❌ Error:", error)

