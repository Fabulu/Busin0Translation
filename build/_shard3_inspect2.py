import struct, json, os, re
BASE="C:/Programmieren/wizardrytranslation"
glyph_map={int(k):v for k,v in json.load(open(BASE+"/data/msg_glyph_map.json",encoding="utf-8")).items()}
for gid_str,info in json.load(open(BASE+"/data/type2_glyph_overrides.json",encoding="utf-8")).items():
    glyph_map[int(gid_str)]=info["t2"]
# What does glyph 0x330, 0x110, 0x3000 decode to?
for g in (0x0,0x330,0x110,0x3000,0x1000,0x3,0x803f,0x40,0xc00,0x334):
    print(hex(g), repr(glyph_map.get(g,"<not in map>")))
