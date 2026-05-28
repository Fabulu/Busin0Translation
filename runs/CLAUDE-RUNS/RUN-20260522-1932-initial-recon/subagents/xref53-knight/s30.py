import struct,os
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
for idx in list(range(34,50))+[2106,2108,2115]:
    fn=None
    import os as o2
    for f in o2.listdir(RD):
        if f.startswith(str(idx).zfill(4)+'_'):fn=o2.path.join(RD,f);break
    if not fn:continue
    with open(fn,'rb') as f:d=f.read()
    i=0
    while i<len(d)-1:
        v=struct.unpack('>H',d[i:i+2])[0]
        if v==0xFFFF:
            av=[];j=i+2
            while j<len(d)-1:
                w=struct.unpack('>H',d[j:j+2])[0]
                if w==0xFFFF:break
                av.append(w)
                j+=2
            tg=[v for v in av if v<0xFFC0]
            for wi in range(len(tg)-37):
                s=tg[wi:wi+38]
                if s[37]!=63 or s[10]!=62:continue
                sc=0
                if s[1]==s[8]:sc+=1
                if s[1]==s[20]:sc+=1
                if s[9]==s[30]:sc+=1
                if s[13]==s[25]:sc+=1
                if s[2]==s[36]:sc+=1
                if sc>=3:
                    print('R%d sc=%d: %s'%(idx,sc,str(s)))
            i=j
        else:i+=2
print('Done')
