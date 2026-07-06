import sys,struct,json
sys.stdout.reconfigure(encoding='utf-8')
pristine=open("../../extracted/packdata_raw/1892_type20.raw",'rb').read()
REC_BASE,REC_STRIDE=0x140,0x130
def rec_name(i):
    rs=REC_BASE+i*REC_STRIDE;o=rs+2;out=[]
    while True:
        v=struct.unpack_from('<H',pristine,o)[0]
        if v==0xFFFF:break
        out.append(v);o+=2
    return out

# Known: the 5 starting party premades. From story: Vera, and 4 others.
# rec0=Vera(ヴェーラ), and recruit-pool gives the kana spelling.
# Records 0-4 katakana glyph indices vs records 6-19 (correct codec).
# Build a glyph->kana map from records 6-19 (these decode correctly with base-193 + KATA_EXTRA)
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def codecB(nv):
    if 193<=nv<=193+44: return KATA[nv-193]
    return KATA_EXTRA.get(nv,f'<{nv}>')

print("Records 0-4 (active party) glyph indices:")
for i in range(5):
    print(f"  rec{i}: {rec_name(i)}  (codecB->{''.join(codecB(v) for v in rec_name(i))})")

print("\nRecords 6-19 (recruit pool) glyph indices + correct kana:")
for i in range(6,20):
    nm=rec_name(i)
    print(f"  rec{i}: {nm}  -> {''.join(codecB(v) for v in nm)}")

# The story starting party of Busin 0 (Wizardry Alternative Neo).
# rec0 Vera. Let's figure the 0-4 codec by assuming each maps to one of the
# known recruit names (same 5 chars appear in pool? No - starting party may differ).
# Find: does rec0 [193,194,232,205] share structure with any pool name?
# Actually maybe records 0-4 ARE the SAME names but in display-glyph (R2100) indices
# already PRE-RESOLVED, while 6-19 are name-VALUE codec.
# Test: active codec char = id-63 for ASCII gave english for pool RAM. 
# For katakana in records 0-4, try mapping to R2100 page0 katakana cells.
# We KNOW rec0=Vera=ヴェーラ. So in codec_0to4: glyph for ヴ,ェ,ー,ラ = ?,?,?,?
# [193,194,232,205]. ヴ=193? ェ=194? ー=232? ラ=205?
print("\nCracking codec0-4 assuming rec0=ヴェーラ:")
print("  193->ヴ, 194->ェ, 232->ー, 205->ラ")
