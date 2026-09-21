import pathlib
path = pathlib.Path(r'D:\SmartFarmerAssistant\probe_export_result.txt')
path.write_text('hello-from-python', encoding='utf-8')
print('hello-from-python')
