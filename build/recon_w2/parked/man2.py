import sys, json
sys.stdout.reconfigure(encoding='utf-8')
man=json.load(open("C:/programmieren/wizardrytranslation/extracted/packdata_resources/manifest.json",encoding="utf-8"))
print("keys for entry 1197:", list(man[1197].keys()))
print(json.dumps(man[1197], indent=1)[:600])
