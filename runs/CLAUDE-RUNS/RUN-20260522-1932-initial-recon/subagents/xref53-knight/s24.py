import struct,os,json
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    c=json.load(f)
mi2=c['msg_resource_indices']
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
r=[]
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
                if w<0xFFC0:g.append(w)
                j+=2
            if 30<=len(g)<=50 and all(x<=1100 for x in g) and len(g)>8:
                if g[1]==g[8] and g[1]>5:
                    r.append([idx,len(g),g[1],g])
            i=j
        else:i+=2
print('Found: %d'%len(r))
for x in r:
    print('R%d l=%d v=%d: %s'%(x[0],x[1],x[2],str(x[3][:20])))
