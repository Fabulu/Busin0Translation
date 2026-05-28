import struct,os,json
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    c=json.load(f)
mi2=c['msg_resource_indices']
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
def ea(data):
    ms=[];i=0
    while i<len(data)-1:
        v=struct.unpack('>H',data[i:i+2])[0]
        if v==0xFFFF or v==0xFFFE:
            g=[];j=i+2
            while j<len(data)-1:
                w=struct.unpack('>H',data[j:j+2])[0]
                if w==0xFFFF or w==0xFFFE:break
                if w<0xFFC0:g.append(w)
                j+=2
            if g:ms.append(g)
            i=j
        else:i+=2
    return ms
r=[]
for idx in mi2:
    p=frf(idx)
    if not p:continue
    with open(p,'rb') as f:d=f.read()
    ms=ea(d)
    for i in range(len(ms)-2):
        a,b,c2=ms[i],ms[i+1],ms[i+2]
        la,lb,lc=len(a),len(b),len(c2)
        tot=la+lb+lc
        if not (35<=tot<=42):continue
        if not (10<=la<=12):continue
        if not (13<=lb<=17):continue
        if not (10<=lc<=14):continue
        hr=False
        for p1 in range(0,3):
            for p2 in range(7,min(la,10)):
                if a[p1]==a[p2]:hr=True
        r.append([idx,i,la,lb,lc,hr,a,b,c2])
print('Candidates: '+str(len(r)))
print('With repeat: '+str(sum(1 for x in r if x[5])))
for x in r:
    if x[5]:
        print('  Res %d pos %d lens=%d/%d/%d'%(x[0],x[1],x[2],x[3],x[4]))
        print('    L0=%s'%str(x[6]))
        print('    L1=%s'%str(x[7]))
        print('    L2=%s'%str(x[8]))
json.dump(r,open(r'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/xref53-knight/c9.json','w'),indent=2)
