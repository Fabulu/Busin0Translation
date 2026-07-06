import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/barkeepoverflow__ee.bin",'rb').read()
# Glyph encoding for boxed dialogue: BE u16 per glyph; ascii glyph = char code? Need glyph map.
# From renderer: glyph<0x8000 drawn; uses metrics table index = glyph (0..0x1B0). So glyph ids are small.
# Let's search for the 0xFFD2 control word as BE bytes 0xFF 0xD2, and dump surrounding u16s.
needle = b'\xff\xd2'
hits=[]
start=0
while True:
    i = ee.find(needle, start)
    if i<0: break
    if i%2==0:  # aligned u16
        hits.append(i)
    start=i+1
print("total FFD2 aligned u16 occurrences:", len(hits))
# Heuristic: dialogue stream has many small u16 (ascii-ish glyph ids 0x20-0x200) around the FFD2.
def score(i):
    s=0
    for j in range(max(0,i-40), i, 2):
        v=struct.unpack_from('>H',ee,j)[0]
        if 0x20<=v<=0x200: s+=1
    for j in range(i+2, i+42, 2):
        v=struct.unpack_from('>H',ee,j)[0]
        if 0x20<=v<=0x200: s+=1
    return s
scored=sorted(hits, key=score, reverse=True)
for i in scored[:8]:
    print(f"\n=== FFD2 at 0x{i:08X} score={score(i)} ===")
    ctx=[]
    for j in range(i-60, i+62, 2):
        v=struct.unpack_from('>H',ee,j)[0]
        mark='<<<' if j==i else ''
        ctx.append(f"0x{v:04X}{mark}")
    print(' '.join(ctx))
