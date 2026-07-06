import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
# hiragana grid: build full char list in 50-on order from the grid stride-57.
# The katakana base in struct: ラ(ra)=193. row layout for katakana KATA string used base 193 for ア? 
# Actually KATA[0]='ア' -> nv 193. So katakana ア=193. Hiragana likely shares a parallel block.
# Hiragana あ would be at some base. Let's brute: search EE for runs of 4 u16 in [95..700] FFFF-terminated
# that are unique. Print those near class data.
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
from collections import Counter
runs=Counter()
locs={}
i=0x100000
while i<0x800000-12:
    v0=struct.unpack_from('<H',ee,i)[0]
    if 95<=v0<=900:
        vals=[v0]; o=i+2; ok=False
        while o<i+12:
            w=struct.unpack_from('<H',ee,o)[0]
            if w==0xFFFF: ok=(len(vals)==4); break
            if not (95<=w<=900): break
            vals.append(w); o+=2
        if ok:
            t=tuple(vals); runs[t]+=1; locs.setdefault(t,[]).append(i)
    i+=2
# よしほく is 4 chars. Print unique 4-runs that occur 1-3 times
print("candidate 4-char runs (count<=3):")
for t,c in runs.items():
    if c<=3:
        print(f"  {t} x{c} @ {[hex(x) for x in locs[t][:4]]}")
