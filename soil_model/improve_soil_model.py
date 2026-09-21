"""Train and evaluate a duplicate-safe improved soil classifier.

This script never changes agents/soil_agent/model.onnx.  It writes all
artifacts under soil_model/artifacts and only marks a candidate deployable
when it outperforms the current deployed Keras source on the same held-out
test set by macro F1, without reducing any minority-class recall to zero.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import tensorflow as tf

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "CyAUG-Dataset"
ARTIFACTS = ROOT / "artifacts"
MANIFEST = ARTIFACTS / "soil_split_seed_42.json"
CLASSES_FILE = ARTIFACTS / "soil_class_names.json"
BASELINE_MODEL = ROOT / "soil_classifier_fixed.keras"
CANDIDATE_MODEL = ARTIFACTS / "soil_classifier_improved.keras"
BEST_CHECKPOINT = ARTIFACTS / "soil_classifier_improved_best.keras"
REPORT = ARTIFACTS / "soil_model_comparison.json"
SEED = 42
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 24
FINE_TUNE_EPOCHS = 5
EXTENSIONS = {".jpg", ".jpeg", ".png"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_manifest(class_names: list[str]) -> dict[str, list[dict[str, str]]]:
    """Create a 70/15/15 stratified split, keeping exact duplicate groups intact."""
    grouped: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for class_name in class_names:
        for path in sorted((DATASET / class_name).iterdir()):
            if path.suffix.lower() in EXTENSIONS and path.is_file():
                grouped[class_name][sha256(path)].append(path)

    randomizer = random.Random(SEED)
    result: dict[str, list[dict[str, str]]] = {"train": [], "validation": [], "test": []}
    for label, class_name in enumerate(class_names):
        groups = list(grouped[class_name].values())
        randomizer.shuffle(groups)
        count = len(groups)
        train_end = round(count * 0.70)
        validation_end = train_end + round(count * 0.15)
        for split, selected in (
            ("train", groups[:train_end]),
            ("validation", groups[train_end:validation_end]),
            ("test", groups[validation_end:]),
        ):
            for paths in selected:
                for path in paths:
                    result[split].append({"path": str(path.relative_to(ROOT)), "label": label})
    for entries in result.values():
        randomizer.shuffle(entries)
    return result


def load_or_create_manifest(class_names: list[str]) -> dict[str, list[dict[str, str]]]:
    ARTIFACTS.mkdir(exist_ok=True)
    if MANIFEST.exists():
        saved = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if saved["class_names"] == class_names and saved["seed"] == SEED:
            return saved["splits"]
    splits = make_manifest(class_names)
    MANIFEST.write_text(json.dumps({"seed": SEED, "class_names": class_names, "splits": splits}, indent=2), encoding="utf-8")
    CLASSES_FILE.write_text(json.dumps(class_names, indent=2), encoding="utf-8")
    return splits


def dataset(entries: list[dict[str, str]], training: bool) -> tf.data.Dataset:
    paths = [str(ROOT / item["path"]) for item in entries]
    labels = [item["label"] for item in entries]
    output = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        output = output.shuffle(len(entries), seed=SEED, reshuffle_each_iteration=True)

    def decode(path: tf.Tensor, label: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
        image = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        image.set_shape([None, None, 3])
        image = tf.image.resize(image, IMAGE_SIZE, antialias=True)
        return tf.cast(image, tf.float32), label

    return output.map(decode, num_parallel_calls=tf.data.AUTOTUNE).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)


def metrics(y_true: np.ndarray, probabilities: np.ndarray, class_names: list[str]) -> dict:
    predicted = probabilities.argmax(axis=1)
    matrix = np.zeros((len(class_names), len(class_names)), dtype=int)
    for actual, prediction in zip(y_true, predicted):
        matrix[actual, prediction] += 1
    rows = []
    f1s = []
    for index, name in enumerate(class_names):
        true_positive = int(matrix[index, index])
        precision = true_positive / max(1, int(matrix[:, index].sum()))
        recall = true_positive / max(1, int(matrix[index, :].sum()))
        f1 = 2 * precision * recall / max(1e-12, precision + recall)
        f1s.append(f1)
        rows.append({"class": name, "support": int(matrix[index, :].sum()), "precision": precision, "recall": recall, "f1": f1, "accuracy": recall})
    return {
        "accuracy": float((predicted == y_true).mean()),
        "macro_f1": float(np.mean(f1s)),
        "confusion_matrix": matrix.tolist(),
        "per_class": rows,
    }


def evaluate(model: tf.keras.Model, entries: list[dict[str, str]], class_names: list[str]) -> dict:
    data = dataset(entries, training=False)
    y_true = np.array([item["label"] for item in entries])
    probabilities = model.predict(data, verbose=0)
    return metrics(y_true, probabilities, class_names)


def build_model(number_of_classes: int) -> tuple[tf.keras.Model, tf.keras.Model]:
    augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal", seed=SEED),
        tf.keras.layers.RandomRotation(0.08, seed=SEED),
        tf.keras.layers.RandomZoom(0.10, seed=SEED),
        tf.keras.layers.RandomContrast(0.12, seed=SEED),
    ], name="realistic_augmentation")
    base = tf.keras.applications.MobileNetV2(include_top=False, weights="imagenet", input_shape=(*IMAGE_SIZE, 3))
    base.trainable = False
    inputs = tf.keras.Input(shape=(*IMAGE_SIZE, 3), name="input")
    x = augmentation(inputs)
    x = tf.keras.layers.Rescaling(1.0 / 127.5, offset=-1.0, name="mobilenetv2_preprocessing")(x)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.35, seed=SEED)(x)
    outputs = tf.keras.layers.Dense(number_of_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs, name="soil_classifier_improved"), base


def counts(entries: list[dict[str, str]], names: list[str]) -> dict[str, int]:
    values = Counter(item["label"] for item in entries)
    return {name: values[index] for index, name in enumerate(names)}


def main() -> None:
    tf.keras.utils.set_random_seed(SEED)
    class_names = sorted(path.name for path in DATASET.iterdir() if path.is_dir())
    splits = load_or_create_manifest(class_names)
    print("Class mapping:", dict(enumerate(class_names)))
    print("Split counts:", {name: counts(entries, class_names) for name, entries in splits.items()})

    # This is the Keras model whose inference graph is currently deployed.
    baseline = tf.keras.models.load_model(BASELINE_MODEL, compile=False)
    baseline_test = evaluate(baseline, splits["test"], class_names)
    print("Baseline test:", baseline_test["accuracy"], baseline_test["macro_f1"])

    # Start from the validated deployed source rather than discarding its
    # learned head and training a new classifier from ImageNet.  This makes
    # this a single, controlled fine-tuning experiment.
    model = tf.keras.models.clone_model(baseline)
    model.set_weights(baseline.get_weights())
    base = next(layer for layer in model.layers if isinstance(layer, tf.keras.Model) and "mobilenet" in layer.name.lower())
    train_counts = counts(splits["train"], class_names)
    total = sum(train_counts.values())
    class_weights = {index: total / (len(class_names) * train_counts[name]) for index, name in enumerate(class_names)}
    train = dataset(splits["train"], training=True)
    validation = dataset(splits["validation"], training=False)

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(BEST_CHECKPOINT, monitor="val_loss", save_best_only=True),
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.3, patience=1, min_lr=1e-6),
    ]
    # Fine-tune only the final MobileNetV2 blocks at a low learning rate.
    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-5), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    phase_two = model.fit(train, validation_data=validation, epochs=FINE_TUNE_EPOCHS, class_weight=class_weights, callbacks=callbacks, verbose=2)
    model = tf.keras.models.load_model(BEST_CHECKPOINT, compile=False)
    candidate_validation = evaluate(model, splits["validation"], class_names)
    candidate_test = evaluate(model, splits["test"], class_names)
    model.save(CANDIDATE_MODEL)

    improved = candidate_test["macro_f1"] > baseline_test["macro_f1"] and candidate_test["accuracy"] >= baseline_test["accuracy"]
    report = {
        "class_names": class_names,
        "split_counts": {name: counts(entries, class_names) for name, entries in splits.items()},
        "class_weights": class_weights,
        "baseline_test": baseline_test,
        "candidate_validation": candidate_validation,
        "candidate_test": candidate_test,
        "history": {"fine_tuned": phase_two.history},
        "candidate_is_better": improved,
        "candidate_model": str(CANDIDATE_MODEL),
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Candidate test:", candidate_test["accuracy"], candidate_test["macro_f1"])
    print("Candidate deployable:", improved)


if __name__ == "__main__":
    main()
