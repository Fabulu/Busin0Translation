import json, os, struct, sys, glob
ROOT=os.path.abspath(".")
sys.path.insert(0, os.path.join(ROOT,"tools"))
import sec1_disasm as S
RAW=os.path.join(ROOT,"extracted","packdata_raw")
GM=json.load(open(os.path.join(ROOT,"data","msg_glyph_map.json"),encoding="utf-8"))
NL={k:v for k,v in json.load(open(os.path.join(ROOT,"data","name_labels.json"),encoding="utf-8")).items() if not k.startswith("_")}
def gl(s): return s.encode("ascii","backslashreplace").decode("ascii") if s else s
def decode(sec2,off,cnt):
    out=[];n=len(sec2)//2
    for i in range(off,off+cnt):
        if i<0 or i>=n: return None
        g=struct.unpack_from(">H",sec2,i*2)[0]
        if g>=0xFB00 or g==0xFFFF: return None
        ch=GM.get(str(g))
        out.append(ch if ch is not None else "<g%d?>"%g)
    return "".join(out)
def groups_of(sec2):
    n=len(sec2)//2;g=[];start=0
    for i in range(n):
        if struct.unpack_from(">H",sec2,i*2)[0]==0xFFFF:g.append((start,i));start=i+1
    return g,start
from collections import Counter
sig=Counter(); ex={}
for p in sorted(glob.glob(os.path.join(RAW,"*_type02.raw"))):
    rid=os.path.basename(p).split("_")[0].lstrip("0")
    d=open(p,"rb").read()
    try:
        ok,instrs,sec1,sec2_off=S.walk_resource(d);recs=S.extract_records(sec1,instrs)
    except Exception: continue
    sec2=d[sec2_off:];groups,trail=groups_of(sec2);gstart={gs for gs,ge in groups}
    n=len(sec2)//2
    for r in recs["label"]:
        off,cnt=r["off"],r["cnt"]
        if cnt<1 or cnt>6 or off+cnt>n: continue
        gids=tuple(struct.unpack_from(">H",sec2,i*2)[0] for i in range(off,off+cnt))
        if any(g>=0xFB00 or g==0xFFFF for g in gids): continue
        # islands STARTING with 297,280,286
        if gids[:3]==(297,280,286):
            sig[gids]+=1
            ex.setdefault(gids,(rid,off in gstart,decode(sec2,off,cnt)))
for gids,c in sig.most_common():
    rid,pre,dec=ex[gids]
    print("x%-3d R%-5s %-6s gids=%-28s map=%-16s decode=%s"%(c,rid,"PREFIX" if pre else "mid",str(list(gids)),repr(NL.get(dec)),gl(dec)))
