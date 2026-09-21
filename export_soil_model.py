import json
from pathlib import Path

import onnx
import tensorflow as tf
import tf2onnx

keras_path = Path(r"D:\SmartFarmerAssistant\soil_model\soil_classifier.keras")
classes_path = Path(r"D:\SmartFarmerAssistant\soil_model\class_names.json")
model_out = Path(r"D:\SmartFarmerAssistant\agents\soil_agent\model.onnx")
class_out = Path(r"D:\SmartFarmerAssistant\agents\soil_agent\class_names.json")
summary_out = Path(r"D:\SmartFarmerAssistant\soil_export_summary.txt")

model = tf.keras.models.load_model(str(keras_path), compile=False)
classes = json.loads(classes_path.read_text(encoding="utf-8"))
class_out.write_text(json.dumps(classes, indent=2), encoding="utf-8")

spec = [tf.TensorSpec(shape=(None, 224, 224, 3), dtype=tf.float32, name="input_1")]
model_proto, _ = tf2onnx.convert.from_keras(model, input_signature=spec, opset=17)
onnx.save(model_proto, str(model_out))

loaded = onnx.load(str(model_out))
summary = {
    "keras_exists": keras_path.exists(),
    "class_count": len(classes),
    "onnx_exists": model_out.exists(),
    "onnx_size": model_out.stat().st_size,
    "graph_present": loaded.graph is not None,
    "node_count": len(loaded.graph.node) if loaded.graph is not None else 0,
    "input_names": [i.name for i in loaded.graph.input] if loaded.graph is not None else [],
    "output_names": [o.name for o in loaded.graph.output] if loaded.graph is not None else [],
}
summary_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
