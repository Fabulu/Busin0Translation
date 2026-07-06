import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
# hiragana guess: maybe base for hiragana is 95.. Let's just print raw vals.
def dec(v):
    if 193<=v<=193+44: return KATA[v-193]
    if v in KATA_EXTRA: return KATA_EXTRA[v]
    if 33<=v<=58: return chr(v-33+65)
    return f'<{v}>'
# The runs found: 0x55fc28, 0x55fe18, 0x5601f2, 0x5603e4, 0x5605d4, 0x5607c2 -> stride 0x1F0!
# 0x55fc28 - 0x55fa38? check stride. Let's find base of this second array.
# 0x5601f2 name -> back to header: name at rs+2 so rs=0x5601f0
for s in range(8):
    rs=0x55FA30+s*0x1F0
    hdr=struct.unpack_from('<H',ee,rs)[0]
    vals=[];o=rs+2
    while o<rs+0x40:
        w=struct.unpack_from('<H',ee,o)[0]
        if w==0xFFFF: break
        vals.append(w); o+=2
    print(f"B-slot{s:2d} @0x{rs:X} hdr={hdr:#06x} vals={vals} -> {''.join(dec(v) for v in vals)}")
