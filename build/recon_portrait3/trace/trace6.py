import sys, struct, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build')
import patch_section1_offsets as P
P._load_tables()
ENG=P._ENG_TABLE; ENG_REV=P._ENG_REV
def enc(ch):
    if ch in ENG: return ENG[ch]
    if ch.lower() in ENG: return ENG[ch.lower()]
    return 31
def _wrap_line(seg,m):
    out=[]
    while len(seg)>m:
        b=seg.rfind(' ',0,m+1)
        if b<=0: b=m
        out.append(seg[:b]); seg=seg[b:].lstrip(' ')
    out.append(seg); return out
def wrap(text,m=16):
    return ' // '.join(' / '.join(l for seg in pg.split(' / ') for l in _wrap_line(seg,m)) for pg in text.split(' // '))
def encode(src):
    w=wrap(src); g=[]
    for pi,page in enumerate(w.split(' // ')):
        if pi>0: g.append(0xFFD2)
        lc=0
        for j,part in enumerate(page.split(' / ')):
            if j>0:
                lc+=1
                if lc>=3: g.append(0xFFD2); lc=0
                else: g.append(0xFFFE)
            for ch in part: g.append(enc(ch))
    return w,g
def show(w):
    o=[]
    for g in w:
        if g==0xFFFE:o.append('|LB|')
        elif g==0xFFD2:o.append('|PB|')
        elif g==0xFFFF:o.append('|FF|')
        elif g>=0xFB00:o.append('<%04X>'%g)
        elif g in ENG_REV:o.append(ENG_REV[g])
        else:o.append('?%d'%g)
    return ''.join(o)

cases={
 'OVERFLOW_narration(569)':"No one was in / sight. Not a / sound, not even / the wind.",
 'MAN_narration(575)':"A man / approached, / staggering on / his feet.",
}
ee=open('build/recon_portrait3/extract/OverflowAndTooLongSpaces__ee.bin','rb').read()
ee2=open('build/recon_portrait3/extract/IThinkManShouldBeHere__ee.bin','rb').read()
for name,src in cases.items():
    w,g=encode(src)
    print(f"\n=== {name} ===")
    print("SRC:",repr(src))
    print("WRAPPED:",repr(w))
    print("ENCODED:",show(g))
    # search both ee files
    prefix=b''.join(struct.pack('>H',x) for x in g[:6])
    for tag,buf in (('OVF',ee),('MAN',ee2)):
        idxs=[m.start() for m in re.finditer(re.escape(prefix),buf)]
        if idxs:
            print(f"  in {tag}-ee @",[hex(i) for i in idxs[:3]])
            i=idxs[0]; end=i
            while struct.unpack_from('>H',buf,end)[0]!=0xFFFF: end+=2
            ww=[struct.unpack_from('>H',buf,j)[0] for j in range(i,end,2)]
            print("    RAM:",show(ww))
