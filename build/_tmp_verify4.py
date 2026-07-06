import json, os, struct, sys, glob
ROOT=os.path.abspath(".")
sys.path.insert(0, os.path.join(ROOT,"tools"))
import sec1_disasm as S
RAW=os.path.join(ROOT,"extracted","packdata_raw")
GM=json.load(open(os.path.join(ROOT,"data","msg_glyph_map.json"),encoding="utf-8"))
def decode(sec2,off,cnt):
    out=[];n=len(sec2)//2
    for i in range(off,off+cnt):
        if i<0 or i>=n: return None
        g=struct.unpack_from(">H",sec2,i*2)[0]
        if g>=0xFB00 or g==0xFFFF: return None
        ch=GM.get(str(g)); out.append(ch if ch is not None else "?")
    return "".join(out)
def groups_of(sec2):
    n=len(sec2)//2;g=[];start=0
    for i in range(n):
        if struct.unpack_from(">H",sec2,i*2)[0]==0xFFFF:g.append((start,i));start=i+1
    return g,start
T4=tuple([297,280,286,290]); T3=tuple([297,280,286])
for rid in ["1194","1196","1197","1198","1203","1354"]:
    p=os.path.join(RAW,rid.zfill(4)+"_type02.raw")
    d=open(p,"rb").read()
    try:
        ok,instrs,sec1,sec2_off=S.walk_resource(d);recs=S.extract_records(sec1,instrs)
    except Exception as e:
        print("R%s walk FAIL: %s"%(rid,e)); continue
    sec2=d[sec2_off:];groups,trail=groups_of(sec2);gstart={gs for gs,ge in groups}
    n=len(sec2)//2
    n4=n3=p4=p3=0
    for r in recs["label"]:
        off,cnt=r["off"],r["cnt"]
        if off+cnt>n: continue
        gids=tuple(struct.unpack_from(">H",sec2,i*2)[0] for i in range(off,off+min(cnt,4)))
        full=tuple(struct.unpack_from(">H",sec2,i*2)[0] for i in range(off,off+cnt))
        if full==T4: 
            n4+=1; 
            if off in gstart:p4+=1
        if full==T3:
            n3+=1
            if off in gstart:p3+=1
    print("R%-5s walk_ok=%s  4glyph-island=%d (prefix %d)  3glyph-island=%d (prefix %d)"%(rid,ok,n4,p4,n3,p3))
