import json
with open('C:/Programmieren/wizardrytranslation/extracted/packdata_resources/manifest.json') as f:
    m = json.load(f)
for idx in [2220, 2221, 2222, 2287, 2288, 2289, 2290, 2291]:
    for r in m:
        if r.get('index') == idx:
            print('idx=%d sec=%d sz=%d file=%s type=%d stride=%d' % (idx, r.get('sector_offset',0), r.get('payload_size',0), r.get('filename','?'), r.get('type_code',0), r.get('stride',0)))
