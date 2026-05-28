import struct,os
p=os.path.join(r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources','0038_type01.bin')
with open(p,'rb') as f:d=f.read()
for i in range(0,len(d)-1,2):
    v=struct.unpack('>H',d[i:i+2])[0]
    if v==0xFFFF:
        for k in range(i,min(i+400,len(d)-1),2):
            vv=struct.unpack('>H',d[k:k+2])[0]
            off=(k-i)//2
            if vv==0xFFFF:print('[%d] FFFF'%off)
            elif vv==0xFFFE:print('[%d] FFFE'%off)
            else:print('[%d] %d'%(off,vv))
        break
