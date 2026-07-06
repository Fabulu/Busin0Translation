#!/usr/bin/env python3
"""Tighter: only 0x14 label slices that are clean PREFIXES of a Section-2 group
(the build's actual nameplate path). Report unmapped decoded JP names.
Also flag walk-failed resources that nonetheless contain group-prefix name
islands (the blind spot).
"""
import json, os, struct, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sec1_disasm as S

RAW = os.path.join(ROOT, "extracted", "packdata_raw")
GLYPH_MAP = json.load(open(os.path.join(ROOT, "data", "msg_glyph_map.json"), encoding="utf-8"))
NL = {k: v for k, v in json.load(open(os.path.join(ROOT, "data", "name_labels.json"), encoding="utf-8")).items() if not k.startswith("_")}

def gloss(s): return s.encode("ascii", "backslashreplace").decode("ascii")

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

hits={}
walkfail_with_islands=0
for p in sorted(glob.glob(os.path.join(RAW,"*_type02.raw"))):
    rid=os.path.basename(p).split("_")[0].lstrip("0")
    d=open(p,"rb").read()
    try:
        ok,instrs,sec1,sec2_off=S.walk_resource(d)
        recs=S.extract_records(sec1,instrs)
    except Exception:
        continue
    sec2=d[sec2_off:]
    groups,trail=groups_of(sec2)
    # map group-start word -> set
    gstart={gs for gs,ge in groups}
    had_island=False
    for r in recs["label"]:
        if r["off"]>=trail: continue          # trailing narration, skip
        # is it a clean prefix: off equals some group start?
        if r["off"] not in gstart: continue
        if r["cnt"]>12: continue               # nameplates are short
        s=decode(sec2,r["off"],r["cnt"])
        if not s or not s.strip(): continue
        had_island=True
        if s in NL: continue
        e=hits.setdefault(s,{"count":0,"res":set()})
        e["count"]+=1; e["res"].add("R"+rid)
    if not ok and had_island: walkfail_with_islands+=1

out=[{"jp":k,"gloss":gloss(k),"count":v["count"],"res":sorted(v["res"])}
     for k,v in sorted(hits.items(),key=lambda x:-x[1]["count"])]
json.dump(out, open(os.path.join(ROOT,"build","_nameislands_unmapped.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("group-prefix UNMAPPED nameplate islands:",len(out))
print("walk-failed resources that still had islands:",walkfail_with_islands)
for L in out:
    print("x%-3d len%-2d %-28s %s"%(L["count"],len(L["jp"]),",".join(L["res"][:6]),L["gloss"]))
