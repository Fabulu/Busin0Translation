import struct,glob
f=glob.glob('extracted/packdata_raw/2654_*.raw')[0]
data=open(f,'rb').read()
# header entries: id(u32) offset(u32) size(u32) reserved(u32) = 16 bytes
# from hex: 00000000 22160000 c0020000 00000000 -> id0 off=0x1622 size=0x2c0
subs=[]
i=0
while i+16<=len(data):
    sid,off,size,r=struct.unpack_from('<IIII',data,i)
    if sid==0 and off==0 and size==0 and i>0: break
    if off>len(data) or size>len(data) or off==0: 
        # likely end of table
        break
    subs.append((sid,off,size)); i+=16
    if sid>500: break
print('subs found:',len(subs))
for sid,off,size in subs[:40]:
    print('sub%d off=0x%X size=0x%X'%(sid,off,size))
