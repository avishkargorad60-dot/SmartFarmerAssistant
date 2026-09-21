import json
import shutil
import traceback
from pathlib import Path

import tensorflow as tf
import tf2onnx
import onnx
import onnxruntime as ort
import numpy as np
from PIL import Image


# ============================================================
# PATHS
# ============================================================

BASE = Path(r"C:\SmartFarmerAssistant")

KERAS_MODEL = BASE / "soil_model" / "soil_classifier_fixed.keras"
CLASS_FILE = BASE / "soil_model" / "class_names_fixed.json"

SAVED_MODEL = BASE / "soil_savedmodel_tmp_fixed"

ONNX_MODEL = BASE / "agents" / "soil_agent" / "model.onnx"
TARGET_CLASSES = BASE / "agents" / "soil_agent" / "class_names.json"

TEST_IMAGE = BASE / "soil_model" / "test_images" / "soil1.png"


# ============================================================
# START
# ============================================================

print("=" * 70)
print("SOIL MODEL - FIXED KERAS -> ONNX EXPORT")
print("=" * 70)

print("TensorFlow :", tf.__version__)
print("tf2onnx    :", tf2onnx.__version__)
print("ONNX       :", onnx.__version__)
print("ONNX Runtime:", ort.__version__)


try:

    # ========================================================
    # CHECK FILES
    # ========================================================

    if not KERAS_MODEL.exists():
        raise FileNotFoundError(
            f"Keras model not found:\n{KERAS_MODEL}"
        )

    if not CLASS_FILE.exists():
        raise FileNotFoundError(
            f"Class file not found:\n{CLASS_FILE}"
        )

    if not TEST_IMAGE.exists():
        raise FileNotFoundError(
            f"Test image not found:\n{TEST_IMAGE}"
        )


    # ========================================================
    # LOAD TRAINED MODEL
    # ========================================================

    print("\n[1] Loading trained model...")

    original_model = tf.keras.models.load_model(
        str(KERAS_MODEL),
        compile=False
    )

    print("MODEL LOADED")
    print("Input shape :", original_model.input_shape)
    print("Output shape:", original_model.output_shape)


    # ========================================================
    # LOAD CLASSES
    # ========================================================

    classes = json.loads(
        CLASS_FILE.read_text(
            encoding="utf-8"
        )
    )

    print("\nClasses:")

    for i, name in enumerate(classes):
        print(f"  {i}: {name}")


    # ========================================================
    # CREATE INFERENCE-ONLY MODEL
    # ========================================================

    print("\n[2] Creating inference-only model...")
    print("Removing training augmentation layer...")

    # Original model structure:
    #
    # 0 = data_augmentation
    # 1 = rescaling
    # 2 = MobileNetV2
    # 3 = GlobalAveragePooling2D
    # 4 = Dropout
    # 5 = Dense
    #
    # We remove layer 0 because RandomFlip/Rotation/Zoom
    # creates the untracked seed-generator resource.

    inputs = tf.keras.Input(
        shape=(224, 224, 3),
        name="input"
    )

    x = original_model.layers[1](inputs)

    x = original_model.layers[2](
        x,
        training=False
    )

    x = original_model.layers[3](x)

    x = original_model.layers[4](
        x,
        training=False
    )

    outputs = original_model.layers[5](x)

    inference_model = tf.keras.Model(
        inputs=inputs,
        outputs=outputs,
        name="soil_classifier_inference"
    )

    print("INFERENCE MODEL CREATED")
    print("Input shape :", inference_model.input_shape)
    print("Output shape:", inference_model.output_shape)


    # ========================================================
    # TEST KERAS INFERENCE MODEL
    # ========================================================

    print("\n[3] Testing Keras inference model...")

    image = Image.open(
        str(TEST_IMAGE)
    ).convert("RGB")

    image = image.resize(
        (224, 224)
    )

    # IMPORTANT:
    # The original model contains a Rescaling layer.
    # Therefore DO NOT divide by 255 here.

    arr = np.array(
        image,
        dtype=np.float32
    )

    arr = np.expand_dims(
        arr,
        axis=0
    )

    keras_result = inference_model(
        arr,
        training=False
    ).numpy()[0]

    keras_index = int(
        np.argmax(keras_result)
    )

    keras_confidence = (
        float(keras_result[keras_index])
        * 100
    )

    print("\nKERAS RESULT")
    print("-" * 40)

    print(
        "Image      :",
        TEST_IMAGE.name
    )

    print(
        "Prediction :",
        classes[keras_index]
    )

    print(
        f"Confidence : {keras_confidence:.2f}%"
    )


    # ========================================================
    # CREATE CONCRETE FUNCTION
    # ========================================================

    print("\n[4] Creating TensorFlow serving function...")

    @tf.function(
        input_signature=[
            tf.TensorSpec(
                shape=[None, 224, 224, 3],
                dtype=tf.float32,
                name="input"
            )
        ]
    )
    def serving_fn(x):

        return inference_model(
            x,
            training=False
        )


    # Force TensorFlow to create the concrete function.

    concrete_fn = serving_fn.get_concrete_function()

    print("CONCRETE FUNCTION CREATED")


    # ========================================================
    # SAVE SAVEDMODEL
    # ========================================================

    if SAVED_MODEL.exists():

        print("\nRemoving old SavedModel...")

        shutil.rmtree(
            SAVED_MODEL
        )

    print("\n[5] Saving inference SavedModel...")

    tf.saved_model.save(
        inference_model,
        str(SAVED_MODEL),
        signatures={
            "serving_default": concrete_fn
        }
    )

    print("SAVED_MODEL_READY")
    print(SAVED_MODEL)


    # ========================================================
    # CONVERT FUNCTION -> ONNX
    # ========================================================

    print("\n[6] Converting TensorFlow function -> ONNX...")

    ONNX_MODEL.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if ONNX_MODEL.exists():

        print("Removing old ONNX model...")

        ONNX_MODEL.unlink()


    input_signature = [
        tf.TensorSpec(
            shape=(None, 224, 224, 3),
            dtype=tf.float32,
            name="input"
        )
    ]


    model_proto, _ = tf2onnx.convert.from_function(
        serving_fn,
        input_signature=input_signature,
        opset=17,
        output_path=str(ONNX_MODEL)
    )

    print("ONNX CONVERSION FINISHED")


    # ========================================================
    # VERIFY ONNX FILE
    # ========================================================

    if not ONNX_MODEL.exists():

        raise RuntimeError(
            "ONNX file was not created."
        )

    onnx_size = ONNX_MODEL.stat().st_size

    print("\nONNX MODEL")
    print("-" * 40)

    print(
        "Path:",
        ONNX_MODEL
    )

    print(
        "Size:",
        onnx_size,
        "bytes"
    )

    if onnx_size == 0:

        raise RuntimeError(
            "ONNX file is EMPTY."
        )


    # ========================================================
    # ONNX CHECKER
    # ========================================================

    print("\n[7] Running ONNX checker...")

    onnx_model = onnx.load(
        str(ONNX_MODEL)
    )

    onnx.checker.check_model(
        onnx_model
    )

    print("ONNX_CHECKER_OK")


    # ========================================================
    # ONNX RUNTIME
    # ========================================================

    print("\n[8] Loading ONNX Runtime...")

    session = ort.InferenceSession(
        str(ONNX_MODEL),
        providers=[
            "CPUExecutionProvider"
        ]
    )

    print("\nINPUTS:")

    for inp in session.get_inputs():

        print(
            " ",
            inp.name,
            inp.shape,
            inp.type
        )


    print("\nOUTPUTS:")

    for out in session.get_outputs():

        print(
            " ",
            out.name,
            out.shape,
            out.type
        )


    # ========================================================
    # TEST ONNX
    # ========================================================

    print("\n[9] Testing ONNX model...")

    input_name = session.get_inputs()[0].name

    onnx_result = session.run(
        None,
        {
            input_name: arr
        }
    )

    predictions = onnx_result[0][0]

    onnx_index = int(
        np.argmax(predictions)
    )

    onnx_confidence = (
        float(predictions[onnx_index])
        * 100
    )


    print("\nONNX RESULT")
    print("-" * 40)

    print(
        "Image      :",
        TEST_IMAGE.name
    )

    print(
        "Prediction :",
        classes[onnx_index]
    )

    print(
        f"Confidence : {onnx_confidence:.2f}%"
    )


    # ========================================================
    # COMPARE KERAS VS ONNX
    # ========================================================

    print("\n[10] Comparing Keras and ONNX...")

    difference = np.max(
        np.abs(
            keras_result - predictions
        )
    )

    print(
        f"Maximum probability difference: {difference:.8f}"
    )

    if keras_index == onnx_index:

        print(
            "PREDICTION MATCH: YES"
        )

    else:

        print(
            "PREDICTION MATCH: NO"
        )

        raise RuntimeError(
            "Keras and ONNX predictions do not match."
        )


    # ========================================================
    # COPY CLASS NAMES
    # ========================================================

    TARGET_CLASSES.write_text(
        json.dumps(
            classes,
            indent=2
        ),
        encoding="utf-8"
    )

    print("\nClass names copied to:")

    print(
        TARGET_CLASSES
    )


    # ========================================================
    # SUCCESS
    # ========================================================

    print("\n" + "=" * 70)
    print("SUCCESS")
    print("=" * 70)

    print("\nYour ONNX model is ready:")
    print(ONNX_MODEL)

    print("\nKeras prediction:")
    print(classes[keras_index])

    print("\nONNX prediction:")
    print(classes[onnx_index])

    print("\nMaximum difference:")
    print(f"{difference:.8f}")


except Exception:

    print("\n" + "=" * 70)
    print("EXPORT FAILED")
    print("=" * 70)

    traceback.print_exc()

    raise