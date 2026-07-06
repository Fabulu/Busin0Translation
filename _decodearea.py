import struct,glob,os,json
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
gid2c={int(k):v for k,v in m.items()}
ov=json.load(open('data/type2_glyph_overrides.json',encoding='utf-8')) if os.path.exists('data/type2_glyph_overrides.json') else {}
for k,v in ov.items(): gid2c[int(k)]=v['t2']
def dg(g):
    if g==0xFFFE: return ' / '
    if g==0xFFD2: return ' // '
    if g==0xFFFF: return '\n##FFFF##\n'
    if g>=0xFB00: return '{c%04X}'%g
    if 0<=g<=94: return chr(g+0x20)
    return gid2c.get(g,'[%04X]'%g)
def sec2(data):
    size=struct.unpack_from('<I',data,0x14)[0]; off=struct.unpack_from('<I',data,0x18)[0]
    return data[off:min(off+size,len(data))]
for res,center in [(1196,0xDC7A),(1197,0x55C),(1203,0x6E0E)]:
    f=glob.glob('extracted/packdata_raw/%04d_type02.raw'%res)[0]
    s2=sec2(open(f,'rb').read())
    a=max(0,center-0x40); b=min(len(s2),center+0xC0)
    words=[struct.unpack_from('>H',s2,i)[0] for i in range(a,b-1,2)]
    txt=''.join(dg(g) for g in words)
    open('_lib_area_R%d.txt'%res,'w',encoding='utf-8').write(txt)
    # ascii: count FFFF groups and show structure (non-jp safe)
    print('R%d: wrote _lib_area_R%d.txt, %d words around 0x%X'%(res,res,len(words),center))
