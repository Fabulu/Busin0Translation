import struct, json, os
BASE="C:/Programmieren/wizardrytranslation"
glyph_map={int(k):v for k,v in json.load(open(BASE+"/data/msg_glyph_map.json",encoding="utf-8")).items()}
for gid_str,info in json.load(open(BASE+"/data/type2_glyph_overrides.json",encoding="utf-8")).items():
    glyph_map[int(gid_str)]=info["t2"]
import glob,re
# translated resource ids in range
trans=set()
for f in glob.glob(BASE+"/data/type2_translated/*.json"):
    if f.endswith('.master'): continue
    try: d=json.load(open(f,encoding="utf-8"))
    except: continue
    if isinstance(d,list):
        for e in d:
            if isinstance(e,dict) and 'resource' in e: trans.add(int(e['resource']))
inrange=sorted(r for r in trans if 912<=r<=1600)
def longest_run(rid):
    p=BASE+f"/extracted/packdata_raw/{rid:04d}_type02.raw"
    if not os.path.exists(p): return None
    data=open(p,'rb').read()
    sz=struct.unpack_from("<I",data,0x14)[0]; off=struct.unpack_from("<I",data,0x18)[0]
    sec2=data[off:min(off+sz,len(data))]
    nw=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(nw)]
    gs=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF: gs.append(words[start:i]);start=i+1
    if start<nw: gs.append(words[start:nw])
    best=0;ndistinct_long=set()
    for grp in gs:
        cur=0;s=[]
        for g in grp:
            if g<=94: ch=chr(g+0x20)
            elif g in glyph_map: ch=glyph_map[g]
            else: ch=None
            if ch is not None and len(ch)==1 and not ch.isspace() and ch not in '　・':
                cur+=1; best=max(best,cur)
            else:
                cur=0
    return best, len(gs)
print("KNOWN-TRANSLATED resources in range (these ARE dialogue): longest readable run")
for rid in inrange:
    r=longest_run(rid)
    if r: print(f"  R{rid}: longest_run={r[0]} groups={r[1]}")
