import json
import shutil
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import tensorflow as tf
import tf2onnx
from PIL import Image

KerasModelPath = Path(r"D:\SmartFarmerAssistant\soil_model\soil_classifier.keras")
SourceClassPath = Path(r"D:\SmartFarmerAssistant\soil_model\class_names.json")
TargetModelPath = Path(r"D:\SmartFarmerAssistant\agents\soil_agent\model.onnx")
TargetClassPath = Path(r"D:\SmartFarmerAssistant\agents\soil_agent\class_names.json")
SavedModelDir = Path(r"D:\SmartFarmerAssistant\soil_savedmodel_tmp")
TestImagePath = Path(r"D:\SmartFarmerAssistant\soil_model\test_images\soil1.png")
ReportPath = Path(r"D:\SmartFarmerAssistant\soil_export_report.json")

if not KerasModelPath.exists():
    raise FileNotFoundError(f"Keras model not found: {KerasModelPath}")
if not SourceClassPath.exists():
    raise FileNotFoundError(f"Source class file not found: {SourceClassPath}")

print(f"Loading Keras model from {KerasModelPath}")
model = tf.keras.models.load_model(str(KerasModelPath), compile=False)

classes = json.loads(SourceClassPath.read_text(encoding="utf-8"))
TargetClassPath.write_text(json.dumps(classes, indent=2), encoding="utf-8")
print(f"Wrote {len(classes)} classes to {TargetClassPath}")

if SavedModelDir.exists():
    shutil.rmtree(SavedModelDir)
SavedModelDir.mkdir(parents=True, exist_ok=True)

input_signature = tf.TensorSpec(shape=(None, 224, 224, 3), dtype=tf.float32, name="input_1")
concrete_fn = tf.function(lambda x: model(x), input_signature=[input_signature])
served_signatures = {"serving_default": concrete_fn.get_concrete_function(input_signature)}

print(f"Saving concrete SavedModel to {SavedModelDir}")
tf.saved_model.save(model, str(SavedModelDir), signatures=served_signatures)

print(f"Converting SavedModel to ONNX at {TargetModelPath}")
# This is the supported path that avoids the tf2onnx.from_keras KeyError
# seen in TensorFlow 2.21 / tf2onnx compatibility.
tf2onnx.convert.from_saved_model(str(SavedModelDir), output_path=str(TargetModelPath), opset=17)

if not TargetModelPath.exists() or TargetModelPath.stat().st_size == 0:
    raise RuntimeError(f"ONNX export failed: output file missing or empty: {TargetModelPath}")

model_proto = onnx.load(str(TargetModelPath))
onnx.checker.check_model(model_proto)

session = ort.InferenceSession(str(TargetModelPath), providers=["CPUExecutionProvider"])

image = Image.open(str(TestImagePath)).convert("RGB").resize((224, 224))
arr = np.array(image, dtype=np.float32) / 255.0
arr = np.expand_dims(arr, axis=0)
input_name = session.get_inputs()[0].name
result = session.run(None, {input_name: arr})

report = {
    "keras_model": str(KerasModelPath),
    "onnx_model": str(TargetModelPath),
    "onnx_exists": TargetModelPath.exists(),
    "onnx_size_bytes": TargetModelPath.stat().st_size,
    "class_count": len(classes),
    "graph_node_count": len(model_proto.graph.node),
    "input_names": [i.name for i in model_proto.graph.input],
    "output_names": [o.name for o in model_proto.graph.output],
    "ort_input_names": [i.name for i in session.get_inputs()],
    "ort_output_names": [o.name for o in session.get_outputs()],
    "ort_input_shapes": [list(i.shape) for i in session.get_inputs()],
    "ort_output_shapes": [list(o.shape) for o in session.get_outputs()],
    "prediction_shape": list(result[0].shape),
    "prediction_sample": result[0][0][:10].tolist(),
}
ReportPath.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(json.dumps(report, indent=2))
