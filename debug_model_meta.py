import os
import onnxruntime as ort

paths = [
    r'D:\SmartFarmerAssistant\agents\soil_agent\model.onnx',
    r'D:\SmartFarmerAssistant\agents\disease_agent\model.onnx',
]

lines = []
for p in paths:
    s = ort.InferenceSession(p, providers=['CPUExecutionProvider'])
    lines.append(f'MODEL {os.path.basename(p)}')
    for i in s.get_inputs():
        lines.append(f'INPUT {i.name} shape={i.shape} type={i.type}')
    for o in s.get_outputs():
        lines.append(f'OUTPUT {o.name} shape={o.shape} type={o.type}')
    lines.append('---')

out_path = r'D:\SmartFarmerAssistant\model_meta_debug.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(out_path)
