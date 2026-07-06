import struct,glob,json
m=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
gid2c={int(k):v for k,v in m.items()}
f=glob.glob('extracted/packdata_raw/2654_*.raw')[0]
data=open(f,'rb').read()
# table: id,size,offset,res (16B)
subs=[]; i=0
while i+16<=len(data):
    sid,size,off,r=struct.unpack_from('<IIII',data,i)
    if off==0 or off>len(data): break
    subs.append((sid,off,size)); i+=16
    if sid>500: break
def ngroups_text(off,size):
    blob=data[off:off+size]; n=size//2
    ffff=0; jp=0; ascii_c=0
    for j in range(n):
        g=struct.unpack_from('>H',blob,j*2)[0]
        if g==0xFFFF: ffff+=1
        elif 0<=g<=94: ascii_c+=1
        elif g in gid2c: jp+=1
    return ffff,jp,ascii_c
for sid,off,size in subs:
    ffff,jp,asc=ngroups_text(off,size)
    flag='<== TEXT' if jp>50 else ''
    print('sub%-2d off=0x%-6X size=0x%-6X ffff=%-4d jp=%-5d ascii=%-5d %s'%(sid,off,size,ffff,jp,asc,flag))
