"""SCRATCH proof-of-fix: R1892 romanize with RAW R2100 glyph codec (NOT +95).
Demonstrates the corrected encoding produces byte-stable records. Writes to scratch only."""
import sys, struct, json, os
sys.stdout.reconfigure(encoding='utf-8')
BASE="C:/programmieren/wizardrytranslation"
PRIS=BASE+"/extracted/packdata_raw/1892_type20.raw"
OUT=BASE+"/build/recon_vera2/synth/1892_RAWGLYPH.raw"
gt=json.load(open(BASE+"/data/english_glyph_table.json",encoding='utf-8'))
labels=json.load(open(BASE+"/data/name_labels.json",encoding='utf-8'))
party=json.load(open(BASE+"/data/r2654_party_names.json",encoding='utf-8'))
allowed=set(party['entries'].values())
REC_BASE=0x140; REC_STRIDE=0x130; NAME_OFF=2; FFFF=0xFFFF
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KX={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def k(v):
    return KATA[v-193] if 193<=v<=237 else KX.get(v,'〓')
def rg(c): return gt.get(c, gt.get(c.lower(),31))
def span(raw,noff):
    o=noff
    while struct.unpack_from('<H',raw,o)[0]!=FFFF: o+=2
    end=o+2
    while end<noff+REC_STRIDE and raw[end]==0xFF: end+=1
    return end-noff
raw=bytearray(open(PRIS,'rb').read())
orig=len(raw); changed=[]
n=(len(raw)-REC_BASE)//REC_STRIDE
for i in range(n):
    rs=REC_BASE+i*REC_STRIDE
    rid=struct.unpack_from('<H',raw,rs)[0]
    noff=rs+NAME_OFF
    vals=[];o=noff
    while o<rs+REC_STRIDE:
        v=struct.unpack_from('<H',raw,o)[0]
        if v==FFFF:break
        vals.append(v);o+=2
    if rid==0 or not vals: continue
    kana=''.join(k(v) for v in vals)
    eng=labels.get(kana)
    if not eng or eng not in allowed: continue
    sp=span(raw,noff); need=(len(eng)+1)*2
    if need>sp:
        print(f"SKIP rec{i} {kana}->{eng} need{need}>field{sp}"); continue
    new=bytearray(b'\xff'*sp); p=0
    for c in eng:
        struct.pack_into('<H',new,p,rg(c)); p+=2   # RAW GLYPH, no +95
    struct.pack_into('<H',new,p,FFFF)
    raw[noff:noff+sp]=new
    changed.append((i,kana,eng,[rg(c) for c in eng]))
assert len(raw)==orig, "size changed!"
open(OUT,'wb').write(raw)
print(f"size stable: {len(raw)}=={orig}  records romanized: {len(changed)}")
for i,kana,eng,g in changed:
    print(f"  rec{i:2d} {kana:<8s} -> {eng:<8s} raw-glyphs={g}")
# verify Vera roundtrip
o=REC_BASE+9*REC_STRIDE+NAME_OFF
vv=[]
while struct.unpack_from('<H',raw,o)[0]!=FFFF:
    vv.append(struct.unpack_from('<H',raw,o)[0]);o+=2
def g2c(g):
    if 33<=g<=58:return chr(g-33+65)
    if 65<=g<=90:return chr(g-65+97)
    return '?'
print("Vera record now renders:", ''.join(g2c(x) for x in vv))
