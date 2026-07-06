import json, os, struct, sys, glob
ROOT = os.path.abspath(".")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sec1_disasm as S
RAW = os.path.join(ROOT, "extracted", "packdata_raw")
GM = json.load(open(os.path.join(ROOT,"data","msg_glyph_map.json"),encoding="utf-8"))
NL = {k:v for k,v in json.load(open(os.path.join(ROOT,"data","name_labels.json"),encoding="utf-8")).items() if not k.startswith("_")}
def gl(s): return s.encode("ascii","backslashreplace").decode("ascii")
def decode(sec2,off,cnt):
    out=[]; n=len(sec2)//2
    for i in range(off,off+cnt):
        if i<0 or i>=n: return None
        g=struct.unpack_from(">H",sec2,i*2)[0]
        if g>=0xFB00 or g==0xFFFF: return None
        ch=GM.get(str(g))
        if ch is None: return "<g%d?>"%g
        out.append(ch)
    return "".join(out)
def groups_of(sec2):
    n=len(sec2)//2; g=[]; start=0
    for i in range(n):
        if struct.unpack_from(">H",sec2,i*2)[0]==0xFFFF: g.append((start,i)); start=i+1
    return g,start
# scan all type02, report ANY label island whose RAW glyph ids include 280 (騎) 
for p in sorted(glob.glob(os.path.join(RAW,"*_type02.raw"))):
    rid=os.path.basename(p).split("_")[0].lstrip("0")
    d=open(p,"rb").read()
    try:
        ok,instrs,sec1,sec2_off=S.walk_resource(d); recs=S.extract_records(sec1,instrs)
    except Exception: continue
    sec2=d[sec2_off:]; groups,trail=groups_of(sec2); gstart={gs for gs,ge in groups}
    for r in recs["label"]:
        off,cnt=r["off"],r["cnt"]
        if cnt>14 or cnt<1: continue
        # raw glyph ids
        n=len(sec2)//2
        if off+cnt>n: continue
        gids=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(off,off+cnt)]
        if 280 in gids:   # 騎
            s=decode(sec2,off,cnt)
            prefix = "PREFIX" if off in gstart else "mid"
            mapped = "MAPPED->%r"%NL.get(s) if s in NL else "UNMAPPED"
            print("R%-5s off=%-6d cnt=%-2d %-7s %-9s gids=%s  decode=%s"%(rid,off,cnt,prefix,mapped,gids,gl(s)))
