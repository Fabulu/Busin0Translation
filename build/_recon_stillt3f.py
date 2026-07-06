import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
os.chdir('C:/programmieren/wizardrytranslation')
ee = open('ramdumps/_stillt3_ex/eeMemory.bin','rb').read()
gmap = json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
def gch(g):
    if g==0xFFFF: return '[END]'
    if g==0xFFFE: return '[LB]'
    if g==0: return '_'
    if 1<=g<95: return chr(0x20+g)
    return gmap.get(str(g), f'<{g}>')

# Search the WHOLE eeMemory for runs of >=4 consecutive 966 (BE u16)
patBE = struct.pack('>H',966)
patLE = struct.pack('<H',966)
for name,pat in (('BE',patBE),('LE',patLE)):
    runs=[]
    i=0
    while True:
        j=ee.find(pat*4, i)
        if j<0: break
        # extend
        k=j
        while ee[k:k+2]==pat: k+=2
        runs.append((j,(k-j)//2))
        i=k
    print(f'=== {name} runs of >=4 x 966 in eeMemory ===', len(runs))
    for off,n in runs[:30]:
        # show context as glyph stream (BE)
        ctx=struct.unpack_from(f'>16H', ee, max(0,off-8))
        print(f'  @0x{off:08x} run {n}  ctxBE:', ' '.join(gch(x) for x in ctx))
