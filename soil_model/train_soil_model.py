import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import json
import os
import numpy as np

# ==============================
# CONFIG
# ==============================

DATASET_DIR = "CyAUG-Dataset"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 20
SEED = 42

# ==============================
# LOAD DATASET
# ==============================

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False
)

class_names = train_ds.class_names
num_classes = len(class_names)

print("\nSoil Classes:")
for i, name in enumerate(class_names):
    print(f"{i} -> {name}")

with open("class_names.json", "w") as f:
    json.dump(class_names, f, indent=4)

# ==============================
# CLASS WEIGHTS
# ==============================

class_counts = {}

for index, class_name in enumerate(class_names):
    class_dir = os.path.join(DATASET_DIR, class_name)

    count = len([
        f for f in os.listdir(class_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])

    class_counts[index] = count

total = sum(class_counts.values())

class_weights = {
    index: total / (num_classes * count)
    for index, count in class_counts.items()
}

print("\nClass counts:")
for index, count in class_counts.items():
    print(f"{index} -> {class_names[index]}: {count}")

print("\nClass weights:")
for index, weight in class_weights.items():
    print(f"{class_names[index]}: {weight:.3f}")

# ==============================
# PERFORMANCE
# ==============================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

# ==============================
# DATA AUGMENTATION
# ==============================

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
])

# ==============================
# MODEL
# ==============================

base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False

inputs = layers.Input(shape=(224, 224, 3))

x = data_augmentation(inputs)
x = preprocess_input(x)

x = base_model(x, training=False)

x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.3)(x)

outputs = layers.Dense(
    num_classes,
    activation="softmax"
)(x)

model = models.Model(inputs, outputs)

# ==============================
# COMPILE
# ==============================

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# ==============================
# TRAIN
# ==============================

print("\n========================================")
print("STARTING SOIL MODEL TRAINING")
print("========================================\n")

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weights
)

# ==============================
# SAVE
# ==============================

model.save("soil_classifier.keras")

print("\n========================================")
print("TRAINING COMPLETED")
print("========================================")
print("Model saved as:")
print("soil_classifier.keras")
print("Classes saved as:")
print("class_names.json")
print("========================================")
