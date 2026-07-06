import struct,glob,json
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
gid2c={int(k):v for k,v in m.items()}
def dg(g):
    if g==0xFFFF: return '|'
    if g==0xFFFE: return ' / '
    if g==0xFFD2: return ' // '
    if 0<=g<=94: return chr(g+0x20)
    return gid2c.get(g,'[%04X]'%g)
f=glob.glob('extracted/packdata_raw/2654_*.raw')[0]
data=open(f,'rb').read()
off=0xA8F0; size=0x3972
blob=data[off:off+size]
n=size//2
words=[struct.unpack_from('>H',blob,i*2)[0] for i in range(n)]
txt=''.join(dg(g) for g in words)
open('_r2654_sub10_full.txt','w',encoding='utf-8').write(txt)
# count FFFF groups
print('sub10: %d words, %d FFFF groups'%(n, txt.count('|')))
# check akusesari ids present
import struct as st
ak=b''.join(st.pack('>H',g) for g in [193,200,206,203,232,93])
print('akusesari in sub10:', hex(blob.find(ak)))
