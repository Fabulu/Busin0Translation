import struct,os,json
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
with open(r'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json') as f:
    c=json.load(f)
mi2=c['msg_resource_indices']
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
def extract_all(data):
    msgs=[]
    i=0
    while i<len(data)-1:
        v=struct.unpack('>H',data[i:i+2])[0]
        if v==0xFFFF or v==0xFFFE:
            g=[]
            j=i+2
            while j<len(data)-1:
                w=struct.unpack('>H',data[j:j+2])[0]
                if w==0xFFFF or w==0xFFFE:break
                if w<0xFFC0:g.append(w)
                j+=2
            if g:msgs.append((g,i,v))
            i=j
        else:i+=2
    return msgs
r2=[]
for idx in mi2:
    p=frf(idx)
    if not p:continue
    with open(p,'rb') as f:d=f.read()
    ms=extract_all(d)
    for i in range(len(ms)-2):
        g0,_,_=ms[i]
        g1,_,_=ms[i+1]
        g2,_,_=ms[i+2]
        if len(g0)==11 and len(g1)==15 and len(g2)==12:
            r2.append([idx,i,g0,g1,g2])
print('Matches: '+str(len(r2)))
for r in r2:
    print('  Res %d pos %d L0=%s L1=%s L2=%s'%(r[0],r[1],str(r[2]),str(r[3]),str(r[4])))
json.dump(r2,open(r'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/xref53-knight/c8.json','w'),indent=2)
