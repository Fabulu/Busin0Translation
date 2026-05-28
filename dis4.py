import struct
path='C:/Programmieren/wizardrytranslation/extracted/packdata_resources/2287_type12.bin'
with open(path,'rb') as f: data=f.read()
hdr=struct.unpack_from('<I',data,0)[0]
print('Hdr:',hdr)
for e in range(3):
    off=4+e*104
    print('Entry %d (0x%04x):'%(e,off))
    for r in range(0,104,16):
        c=data[off+r:off+r+min(16,104-r)]
        print(' +%02d: %s'%(r,' '.join('%02x'%b for b in c)))
print()
for fo in range(0,104,2):
    sc=0
    for e in range(856):
        off=4+e*104+fo
        if off+1>=len(data):break
        v=struct.unpack_from('<H',data,off)[0]
        if (0x829F<=v<=0x82F1)or(0x8340<=v<=0x8396)or(0x889F<=v<=0x9FFC)or(0xE040<=v<=0xEAA4):sc+=1
    if sc>50:print('off+%d: %d/856 SJIS'%(fo,sc))
