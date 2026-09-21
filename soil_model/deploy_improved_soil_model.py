"""Convert and safely deploy the validated improved Soil Keras model."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import tensorflow as tf
import tf2onnx
from PIL import Image

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
CANDIDATE = ARTIFACTS / "soil_classifier_improved.keras"
REPORT = ARTIFACTS / "soil_model_comparison.json"
MANIFEST = ARTIFACTS / "soil_split_seed_42.json"
CLASS_NAMES = ARTIFACTS / "soil_class_names.json"
AGENT_DIR = ROOT.parent / "agents" / "soil_agent"
DEPLOYED = AGENT_DIR / "model.onnx"
DEPLOYED_CLASSES = AGENT_DIR / "class_names.json"
BACKUP = AGENT_DIR / "model.pre_improvement.onnx"
BACKUP_CLASSES = AGENT_DIR / "class_names.pre_improvement.json"
TEMP_ONNX = ARTIFACTS / "soil_classifier_improved.onnx"


def image(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB").resize((224, 224)), dtype=np.float32)[None]


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if not report["candidate_is_better"]:
        raise RuntimeError("Candidate did not meet the independent-test deployment gate.")
    classes = json.loads(CLASS_NAMES.read_text(encoding="utf-8"))
    candidate = tf.keras.models.load_model(CANDIDATE, compile=False)

    # Random augmentation layers carry TensorFlow seed resources and have no
    # place in serving.  Rebuild the deterministic inference path explicitly.
    rescaling = next(layer for layer in candidate.layers if isinstance(layer, tf.keras.layers.Rescaling))
    mobile_net = next(layer for layer in candidate.layers if isinstance(layer, tf.keras.Model) and "mobilenet" in layer.name.lower())
    pooling = next(layer for layer in candidate.layers if isinstance(layer, tf.keras.layers.GlobalAveragePooling2D))
    dropout = next(layer for layer in candidate.layers if isinstance(layer, tf.keras.layers.Dropout))
    classifier = next(layer for layer in candidate.layers if isinstance(layer, tf.keras.layers.Dense))
    inputs = tf.keras.Input(shape=(224, 224, 3), name="input")
    outputs = classifier(dropout(pooling(mobile_net(rescaling(inputs), training=False)), training=False))
    inference_model = tf.keras.Model(inputs, outputs, name="soil_classifier_improved_inference")

    @tf.function(input_signature=[tf.TensorSpec([None, 224, 224, 3], tf.float32, name="input")])
    def serving_fn(batch: tf.Tensor) -> tf.Tensor:
        return inference_model(batch, training=False)

    if TEMP_ONNX.exists():
        TEMP_ONNX.unlink()
    tf2onnx.convert.from_function(
        serving_fn,
        input_signature=[tf.TensorSpec([None, 224, 224, 3], tf.float32, name="input")],
        opset=17,
        output_path=str(TEMP_ONNX),
    )
    if not TEMP_ONNX.exists() or TEMP_ONNX.stat().st_size == 0:
        raise RuntimeError("ONNX conversion did not produce a model.")
    onnx.checker.check_model(str(TEMP_ONNX))
    session = ort.InferenceSession(str(TEMP_ONNX), providers=["CPUExecutionProvider"])
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    maximum_difference = 0.0
    for item in manifest["splits"]["test"][:15]:
        sample = image(ROOT / item["path"])
        keras_output = inference_model(sample, training=False).numpy()[0]
        onnx_output = session.run(None, {session.get_inputs()[0].name: sample})[0][0]
        if int(keras_output.argmax()) != int(onnx_output.argmax()):
            raise AssertionError(f"Keras/ONNX class mismatch for {item['path']}")
        maximum_difference = max(maximum_difference, float(np.max(np.abs(keras_output - onnx_output))))

    # Keep a recoverable copy before replacing the active artifact.
    shutil.copy2(DEPLOYED, BACKUP)
    shutil.copy2(DEPLOYED_CLASSES, BACKUP_CLASSES)
    shutil.copy2(TEMP_ONNX, DEPLOYED)
    DEPLOYED_CLASSES.write_text(json.dumps(classes, indent=2), encoding="utf-8")
    result = {
        "onnx_path": str(DEPLOYED),
        "onnx_size_bytes": DEPLOYED.stat().st_size,
        "onnx_input": [(item.name, item.shape, item.type) for item in session.get_inputs()],
        "onnx_output": [(item.name, item.shape, item.type) for item in session.get_outputs()],
        "onnx_checker": "passed",
        "keras_onnx_images_compared": 15,
        "max_probability_difference": maximum_difference,
        "backup": str(BACKUP),
    }
    (ARTIFACTS / "soil_deployment_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
