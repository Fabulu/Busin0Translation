import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
BASE="C:/programmieren/wizardrytranslation"
PRISTINE=BASE+"/extracted/packdata_raw/1892_type20.raw"
raw=open(PRISTINE,'rb').read()
print("R1892 size:",len(raw))
REC_BASE=0x140; REC_STRIDE=0x130; NAME_OFF=2; FFFF=0xFFFF
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv2k(nv):
    if 193<=nv<=193+44: return KATA[nv-193]
    return KATA_EXTRA.get(nv,f'<{nv}>')
n=(len(raw)-REC_BASE)//REC_STRIDE
print("records:",n)
for i in range(n):
    rs=REC_BASE+i*REC_STRIDE
    rid=struct.unpack_from('<H',raw,rs)[0]
    vals=[]; o=rs+NAME_OFF
    while o<rs+REC_STRIDE:
        v=struct.unpack_from('<H',raw,o)[0]
        if v==FFFF: break
        vals.append(v); o+=1*2
    if rid==0 and not vals: continue
    kana=''.join(nv2k(v) for v in vals)
    # also show struct-glyph form (nv-95)
    glyphs=[v-95 for v in vals]
    print(f"rec{i:2d} id={rid:3d} @file0x{rs+NAME_OFF:X} nv={vals} -> glyphs(nv-95)={glyphs} kana={kana}")
