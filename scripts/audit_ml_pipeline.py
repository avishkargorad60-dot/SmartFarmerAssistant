"""Audit the deployed Soil and Disease inference pipelines.

Run from the repository root with the environment that contains ONNX Runtime:
    soil_model\\venv\\Scripts\\python.exe scripts\\audit_ml_pipeline.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOIL_DATASET = ROOT / "soil_model" / "CyAUG-Dataset"
SOIL_MODEL = ROOT / "agents" / "soil_agent" / "model.onnx"
SOIL_CLASSES = ROOT / "agents" / "soil_agent" / "class_names.json"
DISEASE_MODEL = ROOT / "agents" / "disease_agent" / "model.onnx"
DISEASE_CLASSES = ROOT / "agents" / "disease_agent" / "class_names.json"
DEPLOYED_SOIL_KERAS = ROOT / "soil_model" / "soil_classifier_fixed.keras"


def rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB").resize((224, 224)), dtype=np.float32)


def top_three(values: np.ndarray, labels: list[str]) -> list[tuple[str, float]]:
    return [(labels[int(i)], round(float(values[i]) * 100, 3)) for i in np.argsort(values)[-3:][::-1]]


def audit_soil() -> None:
    labels = json.loads(SOIL_CLASSES.read_text(encoding="utf-8"))
    onnx.checker.check_model(str(SOIL_MODEL))
    session = ort.InferenceSession(str(SOIL_MODEL), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    print("SOIL", session.get_inputs()[0].shape, session.get_outputs()[0].shape)
    correct = total = 0
    for folder in sorted(path for path in SOIL_DATASET.iterdir() if path.is_dir()):
        images = sorted(path for path in folder.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"})[:3]
        predictions = []
        for image in images:
            # Raw RGB is deliberate: the exported graph rescales internally.
            probabilities = session.run(None, {input_name: rgb(image)[None]})[0][0]
            predicted = labels[int(np.argmax(probabilities))]
            predictions.append(predicted)
            correct += predicted == folder.name
            total += 1
            print(f"  {folder.name}/{image.name}: predicted={predicted}; top3={top_three(probabilities, labels)}")
        print(f"  summary {folder.name}: {Counter(predictions)}")
    print(f"SOIL accuracy on sampled labelled data: {correct}/{total} ({100 * correct / total:.1f}%)")

    if "--keras" in sys.argv:
        # TensorFlow is optional for normal production inference, so import it
        # only for this equivalence test.  This is the Keras source used to
        # produce the deployed ONNX model.
        import tensorflow as tf

        keras_model = tf.keras.models.load_model(DEPLOYED_SOIL_KERAS, compile=False)
        compared = 0
        maximum_difference = 0.0
        for folder in sorted(path for path in SOIL_DATASET.iterdir() if path.is_dir()):
            image = next(path for path in sorted(folder.iterdir()) if path.suffix.lower() in {".jpg", ".jpeg", ".png"})
            sample = rgb(image)[None]
            keras_output = keras_model(sample, training=False).numpy()[0]
            onnx_output = session.run(None, {input_name: sample})[0][0]
            if int(np.argmax(keras_output)) != int(np.argmax(onnx_output)):
                raise AssertionError(f"Keras/ONNX class mismatch for {image}")
            maximum_difference = max(maximum_difference, float(np.max(np.abs(keras_output - onnx_output))))
            compared += 1
        print(f"SOIL Keras/ONNX equivalence: {compared} images, max probability difference={maximum_difference:.8g}")


def audit_disease() -> None:
    labels = json.loads(DISEASE_CLASSES.read_text(encoding="utf-8"))
    # This model uses external weights stored in model.onnx.data.
    onnx.checker.check_model(str(DISEASE_MODEL))
    session = ort.InferenceSession(str(DISEASE_MODEL), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    image_path = ROOT / "agents" / "disease_agent" / "test_leaf.png"
    image = rgb(image_path) / 255.0
    image = (image - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array([0.229, 0.224, 0.225], dtype=np.float32)
    logits = session.run(None, {input_name: image.transpose(2, 0, 1)[None]})[0][0]
    probabilities = np.exp(logits - logits.max())
    probabilities /= probabilities.sum()
    print("DISEASE", session.get_inputs()[0].shape, session.get_outputs()[0].shape)
    print(f"  {image_path.name}: top3={top_three(probabilities, labels)}")


if __name__ == "__main__":
    audit_soil()
    audit_disease()
