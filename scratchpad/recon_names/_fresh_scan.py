#!/usr/bin/env python3
"""READ-ONLY fresh nameplate coverage scan with CURRENT glyph map + name_labels."""
import json, os, struct, sys, glob
ROOT = r"C:\Programmieren\wizardrytranslation"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sec1_disasm as S
sys.stdout.reconfigure(encoding="utf-8")

RAW = os.path.join(ROOT, "extracted", "packdata_raw")
GLYPH_MAP = json.load(open(os.path.join(ROOT,"data","msg_glyph_map.json"),encoding="utf-8"))
NL = {k:v for k,v in json.load(open(os.path.join(ROOT,"data","name_labels.json"),encoding="utf-8")).items() if not k.startswith("_")}

def decode(sec2, off, cnt):
    out=[]; n=len(sec2)//2
    for i in range(off, off+cnt):
        if i<0 or i>=n: return None
        g=struct.unpack_from(">H", sec2, i*2)[0]
        if g>=0xFB00 or g==0xFFFF: return None
        ch=GLYPH_MAP.get(str(g))
        if ch is None: return None
        out.append(ch)
    return "".join(out)

def groups_of(sec2):
    n=len(sec2)//2; g=[]; start=0
    for i in range(n):
        if struct.unpack_from(">H", sec2, i*2)[0]==0xFFFF:
            g.append((start,i)); start=i+1
    return g, start

mapped={}     # jp -> {eng, count, res:set}
unmapped={}   # jp -> {count, res:set}
import re
ALL=sorted(glob.glob(os.path.join(RAW,"*_type02.raw")))
for p in ALL:
    _n=int(os.path.basename(p).split("_")[0])
    if not (1190<=_n<=1360): continue
    rid=os.path.basename(p).split("_")[0].lstrip("0")
    d=open(p,"rb").read()
    try:
        ok,instrs,sec1,sec2_off=S.walk_resource(d)
        recs=S.extract_records(sec1,instrs)
    except Exception:
        continue
    sec2=d[sec2_off:]
    groups,trail=groups_of(sec2)
    gstart={gs for gs,ge in groups}
    for r in recs["label"]:
        if r["off"]>=trail: continue
        if r["off"] not in gstart: continue
        if r["cnt"]>12: continue
        s=decode(sec2,r["off"],r["cnt"])
        if not s or not s.strip(): continue
        if s in NL:
            e=mapped.setdefault(s,{"eng":NL[s],"count":0,"res":set()})
            e["count"]+=1; e["res"].add("R"+rid)
        else:
            e=unmapped.setdefault(s,{"count":0,"res":set()})
            e["count"]+=1; e["res"].add("R"+rid)

print("=== UNMAPPED nameplate islands (CURRENT decode, kept as JP) ===")
tot_un=0
for k,v in sorted(unmapped.items(), key=lambda x:-x[1]["count"]):
    g=k.encode("ascii","backslashreplace").decode()
    print("x%-3d len%-2d %-24s %s"%(v["count"],len(k),",".join(sorted(v["res"])[:8]),g))
    tot_un+=v["count"]
print("distinct unmapped=%d  total occ=%d"%(len(unmapped),tot_un))

print("\n=== COLLAPSE: English value shared by multiple distinct JP keys (mapped) ===")
rev={}
for jp,v in mapped.items():
    rev.setdefault(v["eng"],[]).append((jp,v["count"],sorted(v["res"])))
for eng,items in sorted(rev.items(), key=lambda x:-sum(i[1] for i in x[1])):
    total=sum(i[1] for i in items)
    if len(items)>1 or total>=5:
        print("'%s' total_occ=%d across %d distinct JP keys:"%(eng,total,len(items)))
        for jp,c,res in sorted(items,key=lambda x:-x[1]):
            g=jp.encode("ascii","backslashreplace").decode()
            print("    x%-3d %-24s %s"%(c,",".join(res[:8]),g))

print("\n=== FULL MAPPED LIST (all nameplate islands, current decode) ===")
for jp,v in sorted(mapped.items(), key=lambda x:-x[1]["count"]):
    g=jp.encode("ascii","backslashreplace").decode()
    print("x%-3d %-14s <- %-20s %s"%(v["count"], v["eng"], ",".join(sorted(v["res"])[:6]), g))
print("distinct mapped keys=%d"%len(mapped))
# knight family check
print("\n=== KNIGHT-FAMILY keys in name_labels ===")
for k,val in NL.items():
    if 'Knight' in val or 'Commander' in val or '騎士' in k:
        print("  %r -> %r"%(k,val))
