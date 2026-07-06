import struct,glob,json,os
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
gid2c={int(k):v for k,v in m.items()}
def dg(g):
    if g==0xFFFF: return '|'
    if g==0xFFFE: return ' / '
    if 0<=g<=94: return chr(g+0x20)
    return gid2c.get(g,'[%04X]'%g)
f=glob.glob('extracted/packdata_raw/2654_*.raw')[0]
data=open(f,'rb').read()
print('R2654 size',len(data))
# header
print('first 0x40 bytes hex:', data[:0x40].hex())
for off in (0xBE1E, 0xE57C):
    words=[struct.unpack_from('>H',data,off+i*2)[0] for i in range(40)]
    txt=''.join(dg(g) for g in words)
    open('_r2654_at_%X.txt'%off,'w',encoding='utf-8').write(txt)
    print('wrote _r2654_at_%X.txt'%off)
