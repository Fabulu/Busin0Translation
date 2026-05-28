import struct,os,json
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    c=json.load(f)
mi2=c['msg_resource_indices']
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
rc=0;tc=0
for idx in mi2:
    p=frf(idx)
    if not p:continue
    with open(p,'rb') as f:d=f.read()
    i=0
    while i<len(d)-1:
        v=struct.unpack('>H',d[i:i+2])[0]
        if v==0xFFFF:
            g=[];j=i+2
            while j<len(d)-1:
                w=struct.unpack('>H',d[j:j+2])[0]
                if w==0xFFFF:break
                if w!=0xFFFE:g.append(w)
                j+=2
            if 30<=len(g)<=50 and g and all(x<=1100 for x in g):
                tc+=1
                for pp in range(len(g)-7):
                    if g[pp]==g[pp+7] and g[pp]>1:
                        rc+=1;break
            i=j
        else:i+=2
print('30-50 len text: %d, with repeat gap7: %d'%(tc,rc))
