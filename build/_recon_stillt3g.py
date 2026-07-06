import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
os.chdir('C:/programmieren/wizardrytranslation')
ee = open('ramdumps/_stillt3_ex/eeMemory.bin','rb').read()
gmap = json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
def gch(g):
    if g==0xFFFF:return '[END]'
    if g==0xFFFE:return '[LB]'
    if g==0:return '_'
    if 1<=g<95:return chr(0x20+g)
    return gmap.get(str(g),f'<{g}>')

# pattern 966,0 repeated (BE) appears in G411 in R39 at EE 0xe33900 region.
# But the RENDER buffer is elsewhere. Search for '966 0 966 0 966 0' BE and LE.
for name,fmt in (('BE','>H'),('LE','<H')):
    pat = b''.join(struct.pack(fmt,x) for x in [966,0,966,0,966,0])
    i=0; hits=[]
    while True:
        j=ee.find(pat,i)
        if j<0:break
        hits.append(j); i=j+2
    print(f'{name} "966 0 x3" hits:', len(hits), [hex(h) for h in hits[:20]])

# Also: the render text buffer may store glyphs as u16 contiguous (no 0 sep) OR as
# wider records. Search for 966 appearing 6 times within a 64-byte window.
print('\n=== windows with >=6 BE-966 in 80 bytes ===')
patBE=struct.pack('>H',966)
# collect all BE 966 positions
poss=[]
i=0
while True:
    j=ee.find(patBE,i)
    if j<0:break
    poss.append(j); i=j+2
print('total BE 966 positions:', len(poss))
poss.sort()
import bisect
seen=set()
for p in poss:
    cnt=sum(1 for q in poss if p<=q<p+80)
    if cnt>=6 and p not in seen:
        for q in poss:
            if p<=q<p+80: seen.add(q)
        ctx=struct.unpack_from('>40H',ee,p-4)
        print(f'  @0x{p-4:08x} cnt~{cnt}:', ' '.join(gch(x) for x in ctx))
