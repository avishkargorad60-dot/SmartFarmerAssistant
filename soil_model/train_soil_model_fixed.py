import tensorflow as tf
from tensorflow.keras import layers, models
import json
import os
import numpy as np

# ============================================================
# CONFIGURATION
# ============================================================

DATASET_DIR = "CyAUG-Dataset"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

# Start with 10 epochs.
# We can increase later if necessary.
EPOCHS = 10

SEED = 42

# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 70)
print("FIXED SOIL MODEL TRAINING")
print("=" * 70)

print("\nLoading dataset...")

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

class_names = train_ds.class_names

print("\nClasses:")
for i, name in enumerate(class_names):
    print(f"{i} -> {name}")

# Save class names separately
with open("class_names_fixed.json", "w", encoding="utf-8") as f:
    json.dump(class_names, f, indent=4)

# ============================================================
# CLASS WEIGHTS
# ============================================================

# Counts from the dataset
class_counts = {
    "Alluvial_Soil": 693,
    "Arid_Soil": 284,
    "Black_Soil": 1173,
    "Laterite_Soil": 219,
    "Mountain_Soil": 201,
    "Red_Soil": 1126,
    "Yellow_Soil": 1401,
}

total = sum(class_counts.values())
num_classes = len(class_names)

class_weights = {}

for index, name in enumerate(class_names):
    count = class_counts[name]

    # Balanced class weight
    weight = total / (num_classes * count)

    class_weights[index] = weight

print("\nClass weights:")
for index, name in enumerate(class_names):
    print(f"{name:18} -> {class_weights[index]:.4f}")

# ============================================================
# DATA PERFORMANCE
# ============================================================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.shuffle(
    1000,
    seed=SEED
).prefetch(AUTOTUNE)

val_ds = val_ds.prefetch(AUTOTUNE)

# ============================================================
# DATA AUGMENTATION
# ============================================================

data_augmentation = tf.keras.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
    ],
    name="data_augmentation",
)

# ============================================================
# MOBILENETV2
# ============================================================

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet",
)

base_model.trainable = False

# ============================================================
# MODEL
# ============================================================

model = models.Sequential(
    [
        layers.Input(shape=(224, 224, 3)),

        data_augmentation,

        # MobileNetV2 expects inputs in approximately [-1, 1]
        layers.Rescaling(
            1.0 / 127.5,
            offset=-1
        ),

        base_model,

        layers.GlobalAveragePooling2D(),

        layers.Dropout(0.3),

        layers.Dense(
            num_classes,
            activation="softmax"
        ),
    ],
    name="soil_classifier_fixed",
)

# ============================================================
# COMPILE
# ============================================================

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

print("\nModel:")
model.summary()

# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 70)
print("STARTING FIXED TRAINING")
print("=" * 70)

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weights,
)

# ============================================================
# SAVE
# ============================================================

OUTPUT_MODEL = "soil_classifier_fixed.keras"

model.save(OUTPUT_MODEL)

print("\n" + "=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(f"\nModel saved to:")
print(os.path.abspath(OUTPUT_MODEL))

print("\nClass names saved to:")
print(os.path.abspath("class_names_fixed.json"))

print("\nDone.")