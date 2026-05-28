import struct,os
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
p=os.path.join(RD,'0046_type03.bin')
with open(p,'rb') as f:d=f.read()
i=0;mc=0
while i<len(d)-1:
    v=struct.unpack('>H',d[i:i+2])[0]
    if v==0xFFFF:
        g=[];j=i+2
        while j<len(d)-1:
            w=struct.unpack('>H',d[j:j+2])[0]
            if w==0xFFFF:break
            if w<0xFFC0:g.append(w)
            j+=2
        mc+=1
        if len(g)<=8:
            print('M%d l=%d: %s'%(mc,len(g),str(g)))
        else:
            print('M%d l=%d: %s...'%(mc,len(g),str(g[:12])))
        i=j
    else:i+=2
print('Total: %d msgs'%mc)
