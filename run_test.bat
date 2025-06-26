@echo off
call C:\Users\Leinad\miniconda3\Scripts\activate.bat pollux-preview-env
python app/Services/PreviewService/test_imports.py
