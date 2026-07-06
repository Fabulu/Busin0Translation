import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
BASE="C:/programmieren/wizardrytranslation"
bp=BASE+"/build/packdata_resources/1892_type20.raw"
if os.path.exists(bp):
    b=open(bp,'rb').read()
    print("CURRENT SHIPPED build R1892 Vera @0xBF2:",b[0xBF2:0xBFC].hex())
    vals=[struct.unpack_from('<H',b,0xBF2+i*2)[0] for i in range(4)]
    print("  name-values:",vals)
    # render as RAW glyph (what the bar actually does):
    def g2c(g):
        if 33<=g<=58:return chr(g-33+65)
        if 65<=g<=90:return chr(g-65+97)
        return f'[kana{g}]'
    print("  BAR renders these RAW-glyph as:", ''.join(g2c(v) for v in vals))
    print("  (149,164,177,160 are R2100 KATAKANA cells -> garbage, NOT 'Vera')")
else:
    print("no build R1892")
