from pathlib import Path
import tensorflow as tf
import tf2onnx

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "soil_classifier.keras"

OUTPUT_PATH = (
    BASE_DIR.parent
    / "agents"
    / "soil_agent"
    / "model.onnx"
)

print("========================================")
print("SOIL MODEL -> ONNX EXPORT")
print("========================================")

# --------------------------------------------------
# Load trained Keras model
# --------------------------------------------------

print("\nLoading model:")
print(MODEL_PATH)

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

model = tf.keras.models.load_model(MODEL_PATH)

print("Model loaded successfully.")
print("Input :", model.input_shape)
print("Output:", model.output_shape)


# --------------------------------------------------
# Create inference function
# --------------------------------------------------

@tf.function(
    input_signature=[
        tf.TensorSpec(
            shape=[None, 224, 224, 3],
            dtype=tf.float32,
            name="input"
        )
    ]
)
def inference(x):
    return model(x, training=False)


# --------------------------------------------------
# Test tracing
# --------------------------------------------------

print("\nTracing inference function...")

inference.get_concrete_function()

print("Inference function traced successfully.")


# --------------------------------------------------
# Remove old ONNX
# --------------------------------------------------

if OUTPUT_PATH.exists():
    print("\nRemoving old ONNX file...")
    OUTPUT_PATH.unlink()


# --------------------------------------------------
# Convert to ONNX
# --------------------------------------------------

print("\nConverting to ONNX...")

tf2onnx.convert.from_function(
    inference,
    input_signature=[
        tf.TensorSpec(
            [None, 224, 224, 3],
            tf.float32,
            name="input"
        )
    ],
    opset=13,
    output_path=str(OUTPUT_PATH)
)


# --------------------------------------------------
# Verify
# --------------------------------------------------

if not OUTPUT_PATH.exists():
    raise RuntimeError(
        "ONNX file was not created."
    )

size = OUTPUT_PATH.stat().st_size

if size == 0:
    raise RuntimeError(
        "ONNX file was created but is empty."
    )

print("\n========================================")
print("ONNX EXPORT SUCCESSFUL!")
print("========================================")
print("File:")
print(OUTPUT_PATH)
print(f"Size: {size:,} bytes")
print("========================================")