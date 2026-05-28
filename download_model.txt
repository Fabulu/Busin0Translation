import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'
import easyocr
r = easyocr.Reader(["ja","en"], gpu=False)
print("Model loaded OK")
