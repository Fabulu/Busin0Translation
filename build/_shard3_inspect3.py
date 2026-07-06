import struct, json, os, re
BASE="C:/Programmieren/wizardrytranslation"
glyph_map={int(k):v for k,v in json.load(open(BASE+"/data/msg_glyph_map.json",encoding="utf-8")).items()}
for gid_str,info in json.load(open(BASE+"/data/type2_glyph_overrides.json",encoding="utf-8")).items():
    glyph_map[int(gid_str)]=info["t2"]
def readable_runs(grp):
    s=[]
    for g in grp:
        if g<=94: ch=chr(g+0x20)
        elif g in glyph_map: ch=glyph_map[g]
        else: ch=None
        if ch is not None and len(ch)==1 and not ch.isspace() and ch not in '　・':
            s.append(ch)
        else:
            s.append('\n')
    runs=[r for r in "".join(s).split('\n') if len(r)>=4]
    return runs
def groups(rid):
    data=open(BASE+f"/extracted/packdata_raw/{rid:04d}_type02.raw",'rb').read()
    sz=struct.unpack_from("<I",data,0x14)[0]; off=struct.unpack_from("<I",data,0x18)[0]
    sec2=data[off:min(off+sz,len(data))]
    nw=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(nw)]
    gs=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF: gs.append(words[start:i]);start=i+1
    if start<nw: gs.append(words[start:nw])
    return gs
# also a KNOWN-GOOD dialogue resource for comparison
out=[]
for rid in (1196,1063,1089,1079,1055,914):
    gs=groups(rid)
    allruns=[]
    for grp in gs:
        allruns+=readable_runs(grp)
    allruns.sort(key=len,reverse=True)
    out.append(f"R{rid}: groups={len(gs)} total_readable_runs(>=4)={len(allruns)}")
    for r in allruns[:5]:
        out.append("   RUN["+str(len(r))+"]: "+r)
open(BASE+"/build/_shard3_runs.txt","w",encoding="utf-8").write("\n".join(out))
# ascii preview
for line in out:
    print("".join(c if 32<=ord(c)<127 else '?' for c in line)[:100])
