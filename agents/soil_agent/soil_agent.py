import json
import os

# Heavy libraries are imported lazily inside functions to avoid import-time
# failures when running lightweight integration tests without installing
# dependencies like numpy or onnxruntime.

# File paths relative to this module
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model.onnx")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "class_names.json")

# Fallback class names
FALLBACK_CLASS_PATH = os.path.join(
    BASE_DIR,
    "..",
    "..",
    "soil_model",
    "class_names.json"
)


def load_model():
    """Load ONNX soil classification model."""

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Soil model file not found: {MODEL_PATH}"
        )

    if os.path.getsize(MODEL_PATH) == 0:
        raise ValueError(
            f"Soil model file is empty: {MODEL_PATH}. "
            f"Provide a valid ONNX export."
        )

    import onnxruntime as ort

    return ort.InferenceSession(
        MODEL_PATH,
        providers=["CPUExecutionProvider"]
    )


def load_class_names():
    """Load class names from local file, with fallback to soil_model."""

    # Try local class_names.json
    try:
        with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
            data = f.read().strip()

            if data:
                return json.loads(data)

    except Exception:
        pass

    # Fallback to soil_model/class_names.json
    try:
        with open(FALLBACK_CLASS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return []


def _preprocess_image(image_path, input_shape):
    """
    Preprocess image to match the ONNX model input.

    The deployed ONNX model uses:
        224 x 224 RGB images in the original 0-255 range.

    Its graph contains the training model's ``Rescaling(1 / 127.5,
    offset=-1)`` layer, so scaling the pixels here would apply incompatible
    preprocessing and makes unrelated images collapse to Black_Soil.

    The exported ONNX model expects channels-last:
        [1, 224, 224, 3]
    """

    from PIL import Image
    import numpy as np

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image file not found: {image_path}"
        )

    image = Image.open(image_path).convert("RGB")

    # Determine model input shape
    shape = list(input_shape)

    if len(shape) == 4:

        # Expected format:
        # [batch, height, width, channels]
        if shape[3] == 3:

            _, h, w, c = shape

        # Alternative:
        # [batch, channels, height, width]
        elif shape[1] == 3:

            _, c, h, w = shape

        else:
            h, w, c = 224, 224, 3

    elif len(shape) == 3:

        if shape[2] == 3:
            h, w, c = shape

        elif shape[0] == 3:
            c, h, w = shape

        else:
            h, w, c = 224, 224, 3

    else:
        h, w, c = 224, 224, 3

    # Handle dynamic dimensions
    h = int(h) if h is not None else 224
    w = int(w) if w is not None else 224
    c = int(c) if c is not None else 3

    # Resize
    image = image.resize((w, h))

    # Keep raw RGB values.  The ONNX graph performs MobileNetV2's [-1, 1]
    # conversion internally via its exported Rescaling layer.
    arr = np.array(image, dtype=np.float32)

    # Convert HWC -> CHW only if model expects channels-first
    if len(shape) == 4 and shape[1] == 3:

        arr = np.transpose(arr, (2, 0, 1))

    elif len(shape) == 3 and shape[0] == 3:

        arr = np.transpose(arr, (2, 0, 1))

    # Add batch dimension
    arr = np.expand_dims(arr, axis=0)

    return arr.astype(np.float32)


def predict_soil(image_path):
    """
    Predict soil type from an image.

    Returns:
        (soil_type, confidence_percent)
    """

    session = load_model()
    class_names = load_class_names()

    if not class_names:
        raise RuntimeError(
            "No class names available for soil prediction"
        )

    # Get ONNX input information
    inputs = session.get_inputs()

    input_shape = inputs[0].shape
    input_name = inputs[0].name

    # Preprocess image
    image = _preprocess_image(
        image_path,
        input_shape
    )

    # Run ONNX inference
    output = session.run(
        None,
        {
            input_name: image
        }
    )

    # --------------------------------------------------
    # IMPORTANT:
    # The exported ONNX model already outputs SOFTMAX
    # probabilities.
    #
    # DO NOT apply softmax again.
    # --------------------------------------------------

    predictions = output[0][0]

    probs = predictions

    # Find highest probability
    idx = int(probs.argmax())

    confidence = float(
        probs[idx] * 100.0
    )

    # Safety check
    if idx >= len(class_names):
        raise RuntimeError(
            f"Model returned class index {idx}, "
            f"but only {len(class_names)} class names exist."
        )

    soil_label = class_names[idx]

    # Normalize label for crop recommendation agent
    # Example:
    # Black_Soil -> black soil
    soil_label = soil_label.replace(
        "_",
        " "
    ).lower()

    return soil_label, confidence


if __name__ == "__main__":

    img = os.path.join(
        BASE_DIR,
        "test_soil.jpg"
    )

    soil, conf = predict_soil(img)

    print(
        f"Predicted soil: {soil} ({conf:.2f}%)"
    )
