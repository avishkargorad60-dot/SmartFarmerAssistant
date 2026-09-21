import onnxruntime as ort
import numpy as np
import json
from PIL import Image
from pathlib import Path
from collections import Counter


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = Path(r".\agents\soil_agent\model.onnx")
DATASET_PATH = Path(r".\soil_model\CyAUG-Dataset")
CLASS_PATH = Path(r".\agents\soil_agent\class_names.json")

MAX_IMAGES_PER_CLASS = 20


# ============================================================
# LOAD
# ============================================================

with open(CLASS_PATH, "r", encoding="utf-8") as f:
    class_names = json.load(f)

session = ort.InferenceSession(
    str(MODEL_PATH),
    providers=["CPUExecutionProvider"]
)

input_name = session.get_inputs()[0].name


# ============================================================
# TEST
# ============================================================

print("=" * 80)
print("SOIL MODEL MULTI-IMAGE EVALUATION")
print("=" * 80)

print(f"Testing up to {MAX_IMAGES_PER_CLASS} images per class")
print()


total = 0
correct = 0

class_results = {}


for folder in sorted(DATASET_PATH.iterdir()):

    if not folder.is_dir():
        continue

    actual_name = folder.name

    images = sorted([
        p for p in folder.iterdir()
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
        and p.stat().st_size > 0
    ])

    if not images:
        continue

    images = images[:MAX_IMAGES_PER_CLASS]

    predictions = []
    confidences = []

    class_correct = 0

    for image_path in images:

        try:

            img = (
                Image.open(image_path)
                .convert("RGB")
                .resize((224, 224))
            )

            # model.onnx includes Rescaling(1/127.5, offset=-1), so it
            # receives raw RGB values, not already normalised pixels.
            img = np.asarray(
                img,
                dtype=np.float32
            )

            img = np.expand_dims(
                img,
                axis=0
            )

            output = session.run(
                None,
                {
                    input_name: img
                }
            )[0][0]

            prediction_index = int(
                np.argmax(output)
            )

            prediction_name = class_names[
                prediction_index
            ]

            confidence = float(
                output[prediction_index]
            ) * 100

            predictions.append(
                prediction_name
            )

            confidences.append(
                confidence
            )

            total += 1

            if prediction_name == actual_name:
                correct += 1
                class_correct += 1

        except Exception as e:

            print(
                f"ERROR: {image_path.name}: {e}"
            )


    counter = Counter(predictions)

    most_common_prediction, most_common_count = (
        counter.most_common(1)[0]
    )

    accuracy = (
        class_correct / len(images) * 100
    )

    average_confidence = (
        sum(confidences) / len(confidences)
    )

    class_results[actual_name] = {
        "accuracy": accuracy,
        "avg_confidence": average_confidence,
        "most_common": most_common_prediction,
        "distribution": counter
    }

    print("-" * 80)

    print(
        f"ACTUAL CLASS : {actual_name}"
    )

    print(
        f"IMAGES TESTED: {len(images)}"
    )

    print(
        f"CORRECT      : "
        f"{class_correct}/{len(images)}"
    )

    print(
        f"ACCURACY     : "
        f"{accuracy:.2f}%"
    )

    print(
        f"AVG CONFIDENCE: "
        f"{average_confidence:.2f}%"
    )

    print(
        f"MOST COMMON  : "
        f"{most_common_prediction} "
        f"({most_common_count}/{len(images)})"
    )

    print("PREDICTIONS  :")

    for prediction, count in counter.most_common():

        print(
            f"    {prediction:18} "
            f"{count:2} images"
        )


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 80)
print("FINAL RESULT")
print("=" * 80)

overall_accuracy = (
    correct / total * 100
    if total > 0
    else 0
)

print(
    f"Total images tested : {total}"
)

print(
    f"Correct predictions : {correct}"
)

print(
    f"Wrong predictions   : {total - correct}"
)

print(
    f"Overall accuracy    : {overall_accuracy:.2f}%"
)

print()
print("=" * 80)
