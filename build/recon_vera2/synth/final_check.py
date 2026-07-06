import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
# Confirm: array A recs 0-4 == R1892 recs 0-4 verbatim (already done). 
# Confirm Vera rec9 pristine decode = ヴェーラ and patched-correct = Vera raw glyph.
pris=open("C:/programmieren/wizardrytranslation/extracted/packdata_raw/1892_type20.raw",'rb').read()
v=[struct.unpack_from('<H',pris,0xBF2+i*2)[0] for i in range(4)]
print("R1892 Vera rec9 pristine name-values:",v)
KATA_EX={273:'ヴ',270:'ェ',93:'ー',231:'ラ'}
print("  decodes:", ''.join(KATA_EX.get(x,'?') for x in v), "= ヴェーラ = Vera")
# Show the EXACT byte patch
import json
gt=json.load(open("C:/programmieren/wizardrytranslation/data/english_glyph_table.json",encoding='utf-8'))
def rg(c): return gt.get(c, gt.get(c.lower(),31))
for name,rec,off in [("Vera",9,0xBF2),("Erika",10,0xD22),("Konde",11,0xE52),
                     ("Frieder",6,0x862),("Melanie",7,0x992),("Turgot",13,0x10B2)]:
    enc=b''.join(struct.pack('<H',rg(c)) for c in name)+b'\xff\xff'
    print(f"  rec{rec} {name}: file off 0x{off:X} <- {enc.hex()}  (raw glyphs {[rg(c) for c in name]})")
