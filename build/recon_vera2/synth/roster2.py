import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
# stride 0x1F0 starting near 0x55F810? find headers 0x80xx in 0x55E800..0x562000
base=None
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def dec(v):
    if 193<=v<=193+44: return KATA[v-193]
    if v in KATA_EXTRA: return KATA_EXTRA[v]
    if 33<=v<=58: return chr(v-33+65)
    return f'<{v}>'
# scan stride 0x1F0 from 0x55DD20 for 12 slots
for s in range(12):
    rs=0x55DD20+s*0x1F0
    hdr=struct.unpack_from('<H',ee,rs)[0]
    vals=[];o=rs+2
    while o<rs+0x40:
        w=struct.unpack_from('<H',ee,o)[0]
        if w==0xFFFF: break
        vals.append(w); o+=2
    print(f"slot{s:2d} @0x{rs:X} hdr={hdr:#06x} vals={vals} -> {''.join(dec(v) for v in vals)}")
