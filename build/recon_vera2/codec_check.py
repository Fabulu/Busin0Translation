import sys,json
sys.stdout.reconfigure(encoding='utf-8')
BASE="../.."
glyph_table=json.load(open(f"{BASE}/data/english_glyph_table.json",encoding='utf-8'))
print("glyph_table sample:", {k:glyph_table[k] for k in list(glyph_table)[:20] if k in glyph_table})
for ch in "Vera":
    gid = glyph_table.get(ch, glyph_table.get(ch.lower(),31))
    print(f"  '{ch}': gid={gid}, patcher name_val=gid+95={gid+95}")

# The pool's romanized Vera in RAM = [149,164,177,160] with char=id-63
# V=149 -> 149-63=86='V' yes. So RAM glyph index for 'V' = 86+63=149.
# Patcher writes name_val = gid+95. For that to RENDER as glyph 149, we need
# the name-value -> glyph conversion to map name_val -> glyph 149.
# Pool 'V'=149 (glyph index). What gid does glyph_table give 'V'?
gid_V = glyph_table.get('V',glyph_table.get('v',31))
print(f"\n'V': glyph_table gid={gid_V}")
print(f"Patcher writes name_val for V = {gid_V+95}")
print(f"Active/pool RENDERED glyph index for V = 149 (char=id-63 -> id=86+63)")
print(f"BABA active uses char=id+32: B=34 -> glyph 34. ASCII codec there: gid=char-32")
