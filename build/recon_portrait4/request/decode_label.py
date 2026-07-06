import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
gm=json.load(open('data/msg_glyph_map.json',encoding='utf-8')) if __import__('os').path.exists('data/msg_glyph_map.json') else {}
# build reverse: glyph_id(int)->char
rev={}
for k,v in gm.items():
    try: rev[int(k)]=v
    except: 
        try: rev[int(v)]=k
        except: pass
def sec2(path):
    d=open(path,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[s2:]
def grp(s2,off,cnt):
    # off/cnt are in WORDS (u16). read cnt words from word-offset off
    out=[]
    for i in range(cnt):
        w=struct.unpack_from('>H',s2,(off+i)*2)[0]
        out.append(w)
    return out
def render(words):
    s=''
    for w in words:
        if w in rev: s+=rev[w]
        elif w==0: s+=' '
        elif w>=0xFB00: s+='[%04X]'%w
        else: s+='{%d}'%w
    return s
for tag,p in (('JP','extracted/packdata_raw/1197_type02.raw'),('CUR','build/packdata_resources/1197_type02.raw')):
    s2=sec2(p)
    print(f"=== {tag} ===")
    if tag=='JP':
        for off,cnt in ((0x0FEE,3),(0x0FF1,4)):
            w=grp(s2,off,cnt); print(f"  off=0x{off:X} cnt={cnt}: {w} -> {render(w)!r}")
    else:
        for off,cnt in ((0x161B,3),(0x161E,5)):
            w=grp(s2,off,cnt); print(f"  off=0x{off:X} cnt={cnt}: {w} -> {render(w)!r}")
