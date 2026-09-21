@echo off
setlocal
"D:\SmartFarmerAssistant\soil_model\venv\Scripts\python.exe" -c "import tensorflow as tf; print('TF', tf.__version__)" > "D:\SmartFarmerAssistant\export_run.txt" 2>&1
exit /b %ERRORLEVEL%
