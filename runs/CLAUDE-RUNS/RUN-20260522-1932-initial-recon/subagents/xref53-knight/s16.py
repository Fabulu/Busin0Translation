import struct,os,json
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    c=json.load(f)
mi2=c['msg_resource_indices']
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
text_res=[]
for idx in mi2:
    p=frf(idx)
    if not p:continue
    with open(p,'rb') as f:d=f.read()
    i=0;tm=0;tt=0
    while i<len(d)-1:
        v=struct.unpack('>H',d[i:i+2])[0]
        if v==0xFFFF:
            g=[];j=i+2
            while j<len(d)-1:
                w=struct.unpack('>H',d[j:j+2])[0]
                if w==0xFFFF:break
                if w!=0xFFFE:g.append(w)
                j+=2
            tt+=1
            if g and all(x<=1100 for x in g):tm+=1
            i=j
        else:i+=2
    if tm>10:text_res.append([idx,tm,tt])
print('Real text resources:')
for r in sorted(text_res,key=lambda x:-x[1]):
    print('  R%d: %d/%d'%(r[0],r[1],r[2]))
