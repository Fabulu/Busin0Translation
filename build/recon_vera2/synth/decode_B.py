import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
# english_glyph_table: A=33..Z=58, a=65..z=90, space=0. So glyph->char:
def g2c(g):
    if g==0: return ' '
    if 33<=g<=58: return chr(g-33+ord('A'))
    if 65<=g<=90: return chr(g-65+ord('a'))
    if 16<=g<=25: return chr(g-16+ord('0'))
    return f'[{g}]'
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def kana(v):
    if 193<=v<=237: return KATA[v-193]
    return KATA_EXTRA.get(v,f'<{v}>')
print("Array B decoded as name_val (glyph = nv-95):")
for s in range(20):
    rs=0x55FA30+s*0x1F0
    hdr=struct.unpack_from('<H',ee,rs)[0]
    vals=[];o=rs+2
    while o<rs+0x40:
        w=struct.unpack_from('<H',ee,o)[0]
        if w==0xFFFF: break
        vals.append(w); o+=2
    if not vals and hdr==0: continue
    ascii_form=''.join(g2c(v-95) for v in vals)
    kana_form=''.join(kana(v) for v in vals)
    print(f"B{s:2d} @0x{rs:X} hdr={hdr:#06x} nv={vals}")
    print(f"     ascii(nv-95)={ascii_form!r}  katakana(raw)={kana_form!r}")
