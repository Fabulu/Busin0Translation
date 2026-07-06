import struct,glob,os,json
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
gid2c={int(k):v for k,v in m.items()}
ov=json.load(open('data/type2_glyph_overrides.json',encoding='utf-8')) if os.path.exists('data/type2_glyph_overrides.json') else {}
def dg(g):
    if g==0xFFFE: return ' / '
    if g==0xFFD2: return ' // '
    if g==0xFFFF: return '|FFFF|'
    if g>=0xFB00: return '{%04X}'%g
    if 0<=g<=94: return chr(g+0x20)
    return gid2c.get(g,'[%04X]'%g)
f=glob.glob('extracted/packdata_raw/0034_*.raw')[0]
data=open(f,'rb').read()
size=struct.unpack_from('<I',data,0x14)[0]; off=struct.unpack_from('<I',data,0x18)[0]
print('R34 sec2 off=0x%X size=0x%X filelen=0x%X'%(off,size,len(data)))
s2=data[off:off+size]
hit=0x7EA
# walk backward to FFFF, forward to FFFF
def w(i): return struct.unpack_from('>H',s2,i)[0]
a=hit
while a>=2 and w(a-2)!=0xFFFF: a-=2
b=hit
while b<len(s2)-2 and w(b)!=0xFFFF: b+=2
words=[w(i) for i in range(a,b,2)]
txt=''.join(dg(g) for g in words)
open('_r34_library_body.txt','w',encoding='utf-8').write(txt)
print('group sec2@0x%X..0x%X  %d glyphs -> _r34_library_body.txt'%(a,b,len(words)))
