import json, re, sys
sys.path.insert(0, '.')
# The full translation logic is at /tmp/translate_batch08.py
# Execute it via exec since bash can't find /tmp on Windows
with open(r'\\tmp\translate_batch08.py', 'r', encoding='utf-8') as f:
    exec(f.read())
