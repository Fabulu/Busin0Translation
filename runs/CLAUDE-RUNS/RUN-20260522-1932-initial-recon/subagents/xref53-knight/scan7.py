import struct,os,json
RD=r"C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
with open(r"C:/Programmieren/wizardrytranslation/dumps/resource_classification.json") as f:
    c=json.load(f)
mi2=c["msg_resource_indices"]
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+"_"):return os.path.join(RD,fn)
    return None
def pm(d):
    ms=[];i=0
    while i<len(d)-1:
        v=struct.unpack(">H",d[i:i+2])[0]
        if v==0xFFFF:
            g=[];j=i+2
            while j<len(d)-1:
                w=struct.unpack(">H",d[j:j+2])[0]
                if w==0xFFFF:break
                if w!=0xFFFE:g.append(w)
                j+=2
            ms.append((g,i));i=j
        else:i+=2
    return ms
r1=[];r2=[]
for idx in mi2:
    p=frf(idx)
    if not p:continue
    with open(p,"rb") as f:d=f.read()
    ms=pm(d)
    for mi,(g,o) in enumerate(ms):
        if len(g)!=38:continue
        if g[37]!=63:continue
        if g[1]==g[8]==g[21]:
            r2.append([idx,mi,g])
            if g[9]==g[31] and g[14]==g[26]:
                r1.append([idx,mi,g])
                print("STRICT: Res %d msg %d: %s"%(idx,mi,str(g)))
print("Strict: "+str(len(r1)))
print("Relaxed (p1=8=21,p37=63): "+str(len(r2)))
for r in r2:
    print("  Res %d msg %d: %s"%(r[0],r[1],str(r[2])))
json.dump({"strict":r1,"relaxed":r2},open(r"C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/xref53-knight/c7.json","w"),indent=2)

