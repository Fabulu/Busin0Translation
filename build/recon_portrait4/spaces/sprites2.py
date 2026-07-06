import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/Toolongspaces__ee.bin','rb').read()
t=json.load(open('data/english_glyph_table.json')); rev={v:k for k,v in t.items()}
def rd16(a): return struct.unpack_from('<H',ee,a)[0]
def rds16(a): return struct.unpack_from('<h',ee,a)[0]
sprbuf=0x11F5540
glyphstream=0x11E0A9E
cnt=313
# decode the glyph stream (BE u16) for labeling
glyphs=struct.unpack_from('>%dH'%cnt,ee,glyphstream)
# dump first ~40 sprites: try several field layouts
print("idx glyph char | sprite 0xC bytes (as 6x u16 LE)")
for i in range(40):
    base=sprbuf+i*0xC
    ws=[rd16(base+2*k) for k in range(6)]
    g=glyphs[i] if i<cnt else 0
    ch=rev.get(g,'{%04X}'%g)
    print("%3d %04X %-3s | "%(i,g,ch)+" ".join("%5d"%(struct.unpack_from('<h',ee,base+2*k)[0]) for k in range(6)))
