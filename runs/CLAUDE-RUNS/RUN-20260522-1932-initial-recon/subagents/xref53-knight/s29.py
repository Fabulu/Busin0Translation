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
            tg=[v for v in av if v<0xFFC0 and v<=858]
            for tlen in range(35,43):
                for wi in range(len(tg)-tlen+1):
                    s=tg[wi:wi+tlen]
                    if len(set(s))<15:continue
                    if s[1]==s[8] and s[1]>5:
                        print('l=%d R%d u=%d v=%d: %s'%(tlen,idx,len(set(s)),s[1],str(s[:15])))
            i=j
        else:i+=2
print('Done')
