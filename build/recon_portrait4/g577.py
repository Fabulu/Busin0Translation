import sys, struct, os, json
sys.stdout.reconfigure(encoding='utf-8')
RAW='extracted/packdata_raw'
def groups_of(res):
    raw=open(f'{RAW}/{res:04d}_type02.raw','rb').read()
    sec2_size=struct.unpack_from('<I',raw,0x14)[0]
    sec2_off=struct.unpack_from('<I',raw,0x18)[0]
    sec2=raw[sec2_off:sec2_off+sec2_size]
    n=len(sec2)//2
    words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    grps=[];start=0
    for i in range(n):
        if words[i]==0xFFFF: grps.append(words[start:i]);start=i+1
    return grps
g=groups_of(1196)
# load glyph map for decode
gm=json.load(open('data/msg_glyph_map.json',encoding='utf-8')) if os.path.isfile('data/msg_glyph_map.json') else {}
inv={int(k):v for k,v in gm.items()} if gm else {}
for gi in [569,575,577]:
    grp=g[gi]
    print(f"--- R1196 g{gi} ({len(grp)} words) ---")
    s=' '.join(f'{w:04X}' for w in grp)
    print(s[:400])
    # decode glyphs
    dec=''
    for w in grp:
        if w>=0xFB00: dec+=f'[{w:04X}]'
        else: dec+=inv.get(w,'?')
    print('decoded:',dec[:200])
