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
# all distinct short PREFIX islands across all resources, count freq, show unmapped
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
        if off not in gstart: continue   # PREFIX only
        if cnt<2 or cnt>5 or off+cnt>n: continue
        gids=tuple(struct.unpack_from(">H",sec2,i*2)[0] for i in range(off,off+cnt))
        if any(g>=0xFB00 or g==0xFFFF for g in gids): continue
        sig[gids]+=1
        ex.setdefault(gids,(rid,decode(sec2,off,cnt)))
# show the most common short prefixes not yet mapped
for gids,c in sig.most_common(50):
    rid,dec=ex[gids]
    if dec in NL: continue
    print("x%-3d R%-5s gids=%-30s decode=%s"%(c,rid,str(list(gids)),gl(dec)))
