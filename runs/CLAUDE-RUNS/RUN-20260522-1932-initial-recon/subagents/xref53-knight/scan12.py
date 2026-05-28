import struct,os,json
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    c=json.load(f)
mi2=c['msg_resource_indices']
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
def pm(data):
    ms=[];i=0
    while i<len(data)-1:
        v=struct.unpack('>H',data[i:i+2])[0]
        if v==0xFFFF:
            g=[];j=i+2
            while j<len(data)-1:
                w=struct.unpack('>H',data[j:j+2])[0]
                if w==0xFFFF:break
                if w!=0xFFFE:g.append(w)
                j+=2
            ms.append((g,i));i=j
        else:i+=2
    return ms
r2=[]
for idx in mi2:
    p=frf(idx)
    if not p:continue
    with open(p,'rb') as f:d=f.read()
    ms=pm(d)
    for mi,(g,o) in enumerate(ms):
        if len(g)!=38:continue
        if any(v>1100 for v in g):continue
        if g[1]==g[8]==g[20]:
            s=0
            if g[9]==g[30]:s+=1
            if g[13]==g[25]:s+=1
            if g[2]==g[36]:s+=1
            r2.append([idx,mi,s,g])
print('p1=8=20: '+str(len(r2)))
for x in r2:
    print('  Res %d msg %d score=%d: %s'%(x[0],x[1],x[2],str(x[3])))
