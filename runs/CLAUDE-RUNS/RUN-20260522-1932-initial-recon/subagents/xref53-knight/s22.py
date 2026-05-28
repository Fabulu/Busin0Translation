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
            g=[];j=i+2
            while j<len(d)-1:
                w=struct.unpack('>H',d[j:j+2])[0]
                if w==0xFFFF:break
                if w<0xFFC0:g.append(w)
                j+=2
            if len(g)==38 and all(x<=858 for x in g):
                if g[1]==g[8]==g[20]:
                    s=0
                    if g[9]==g[30]:s+=1
                    if g[13]==g[25]:s+=1
                    if g[2]==g[36]:s+=1
                    print('MATCH R%d s=%d g=%s'%(idx,s,str(g)))
            i=j
        else:i+=2
print('Done')
