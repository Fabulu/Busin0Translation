import struct,os,json
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    c=json.load(f)
mi2=c['msg_resource_indices']
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
c38=0
all38=[]
for idx in range(34,50):
    if idx not in mi2:continue
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
                g.append(w)
                j+=2
            rg=[x for x in g if x!=0xFFFE]
            if len(rg)==38 and all(x<=1100 for x in rg):
                c38+=1
                eq18=rg[1]==rg[8]
                eq120=rg[1]==rg[20] if len(rg)>20 else False
                all38.append([idx,eq18,eq120,rg])
            i=j
        else:i+=2
print('38-glyph msgs in 34-49: '+str(c38))
for x in all38:
    print('R%d p1=p8:%s p1=p20:%s %s'%(x[0],x[1],x[2],str(x[3][:15])+'...'))
