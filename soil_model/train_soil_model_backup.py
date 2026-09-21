import tensorflow as tf
from tensorflow.keras import layers, models
import json
import os

# ==============================
# CONFIGURATION
# ==============================

DATASET_DIR = "CyAUG-Dataset"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 20

# ==============================
# LOAD DATASET
# ==============================

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=42,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

class_names = train_ds.class_names

print("\nSoil Classes:")
for i, name in enumerate(class_names):
    print(i, "->", name)

# Save class names
with open("class_names.json", "w") as f:
    json.dump(class_names, f, indent=4)

# ==============================
# PERFORMANCE
# ==============================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.cache().shuffle(1000).prefetch(
    buffer_size=AUTOTUNE
)

val_ds = val_ds.cache().prefetch(
    buffer_size=AUTOTUNE
)

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

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False

model = models.Sequential([
    data_augmentation,

    layers.Rescaling(1.0 / 255),

    base_model,

    layers.GlobalAveragePooling2D(),

    layers.Dropout(0.2),

    layers.Dense(len(class_names), activation="softmax")
])

# ==============================
# COMPILE
# ==============================

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# ==============================
# TRAIN
# ==============================

print("\nStarting training...\n")

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS
)

# ==============================
# SAVE MODEL
# ==============================

model.save("soil_classifier.keras")

print("\n================================")
print("Training completed!")
print("Model saved as soil_classifier.keras")
print("Classes saved as class_names.json")
print("================================")