import struct,os,json
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    c=json.load(f)
mi2=c['msg_resource_indices']
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
for idx in mi2:
    p=frf(idx)
    if not p:continue
    with open(p,'rb') as f:d=f.read()
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
                if s[1]==s[8]==s[20] and s[1]>5:
                    sc=0
                    if s[9]==s[30]:sc+=1
                    if s[13]==s[25]:sc+=1
                    if s[2]==s[36]:sc+=1
                    if sc>=2:
                        print('R%d sc=%d: %s'%(idx,sc,str(s)))
            i=j
        else:i+=2
print('Done')
