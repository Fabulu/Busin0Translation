import struct, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("C:/Programmieren/wizardrytranslation/extracted/packdata_resources/0046_type03.bin", "rb") as f:
    data = f.read()
with open("C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json", "r", encoding="utf-8") as f:
    glyph_map = json.load(f)

katakana_inferred = {}
basic = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
for i, ch in enumerate(basic): katakana_inferred[193+i] = ch
daku = "ガギグゲゴザジズゼゾダヂヅデド"
for i, ch in enumerate(daku): katakana_inferred[239+i] = ch
handaku = "バビブベボパピプペポ"
for i, ch in enumerate(handaku): katakana_inferred[254+i] = ch
small_k = "ャュョァィゥェォッヴ"
for i, ch in enumerate(small_k): small_k  # placeholder
print("script loaded")

