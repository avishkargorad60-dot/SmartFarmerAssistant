import json
import shutil
import traceback
from pathlib import Path

import onnx
import onnxruntime as ort
import tensorflow as tf
import tf2onnx
from PIL import Image
import numpy as np

KerasModelPath = Path(r"D:\SmartFarmerAssistant\soil_model\soil_classifier.keras")
SourceClassPath = Path(r"D:\SmartFarmerAssistant\soil_model\class_names.json")
TargetModelPath = Path(r"D:\SmartFarmerAssistant\agents\soil_agent\model.onnx")
TargetClassPath = Path(r"D:\SmartFarmerAssistant\agents\soil_agent\class_names.json")
SavedModelDir = Path(r"D:\SmartFarmerAssistant\soil_savedmodel_tmp")
TestImagePath = Path(r"D:\SmartFarmerAssistant\soil_model\test_images\soil1.png")
LogPath = Path(r"D:\SmartFarmerAssistant\soil_export_log.txt")

try:
    print('START')
    print('TF', tf.__version__)
    print('TF2ONNX', tf2onnx.__version__)
    if not KerasModelPath.exists():
        raise FileNotFoundError(f"Keras model not found: {KerasModelPath}")
    if not SourceClassPath.exists():
        raise FileNotFoundError(f"Class file not found: {SourceClassPath}")

    model = tf.keras.models.load_model(str(KerasModelPath), compile=False)
    classes = json.loads(SourceClassPath.read_text(encoding='utf-8'))
    TargetClassPath.write_text(json.dumps(classes, indent=2), encoding='utf-8')
    print('CLASSES', len(classes))

    if SavedModelDir.exists():
        shutil.rmtree(SavedModelDir)
    SavedModelDir.mkdir(parents=True, exist_ok=True)
    tf.saved_model.save(model, str(SavedModelDir))
    print('SAVED_MODEL_READY', SavedModelDir)

    tf2onnx.convert.from_saved_model(str(SavedModelDir), output_path=str(TargetModelPath), opset=17)
    print('POST_CONVERT_EXISTS', TargetModelPath.exists(), 'SIZE', TargetModelPath.stat().st_size if TargetModelPath.exists() else 0)

    onnx.load(str(TargetModelPath))
    onnx.checker.check_model(onnx.load(str(TargetModelPath)))
    print('ONNX_CHECKER_OK')

    sess = ort.InferenceSession(str(TargetModelPath), providers=['CPUExecutionProvider'])
    print('INPUTS', [(i.name, i.shape, i.type) for i in sess.get_inputs()])
    print('OUTPUTS', [(o.name, o.shape, o.type) for o in sess.get_outputs()])

    image = Image.open(str(TestImagePath)).convert('RGB').resize((224, 224))
    arr = np.array(image, dtype=np.float32) / 255.0
    arr = np.expand_dims(arr, axis=0)
    in_name = sess.get_inputs()[0].name
    result = sess.run(None, {in_name: arr})
    print('PRED_SHAPE', result[0].shape)
    print('PRED_SAMPLE', result[0][0][:10].tolist())

    print('SUCCESS')
except Exception:
    LogPath.write_text(traceback.format_exc(), encoding='utf-8')
    print(traceback.format_exc())
    raise
