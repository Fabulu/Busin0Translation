"""Shard 1 refined scan: distinguish real dialogue from binary in R761-911.
Real dialogue = a CONTIGUOUS run of mapped glyphs (not hex placeholders) with
JP density. Binary noise = isolated mapped glyphs amid [XXXX] words."""
import struct, json, os, re, sys

BASE = "C:/Programmieren/wizardrytranslation"
RAW_DIR = os.path.join(BASE, "extracted/packdata_raw")

glyph_map = {int(k): v for k, v in json.load(open(os.path.join(BASE,"data/msg_glyph_map.json"),encoding="utf-8")).items()}
ovp = os.path.join(BASE,"data/type2_glyph_overrides.json")
if os.path.exists(ovp):
    for k,info in json.load(open(ovp,encoding="utf-8")).items():
        glyph_map[int(k)] = info["t2"]

import glob
trans_res=set(); trans_msg=set()
for f in glob.glob(os.path.join(BASE,"data/type2_translated/*.json")):
    if f.endswith(".master"): continue
    try: d=json.load(open(f,encoding="utf-8"))
    except: continue
    if isinstance(d,list):
        for it in d:
            if isinstance(it,dict) and it.get("resource") is not None:
                trans_res.add(it["resource"])
                if it.get("msg_index") is not None and (it.get("english") or "").strip():
                    trans_msg.add((it["resource"], it["msg_index"]))

JP_RE = re.compile(r"[぀-ゟ゠-ヿ㐀-鿿]")  # hira, kata, CJK

def is_mapped(g):
    return (0<=g<=94) or (g in glyph_map)
def is_jp_glyph(g):
    v=glyph_map.get(g)
    return bool(v) and bool(JP_RE.match(v))
def gchar(g):
    if g==0xFFFE: return " / "
    if g==0xFFD2: return " // "
    if 0<=g<=94: return chr(g+0x20)
    return glyph_map.get(g, f"[{g:04X}]")

def best_run(grp):
    """Return (run_len, jp_in_run, run_glyphs) for the longest contiguous mapped (non-placeholder, non-space) run."""
    best=(0,0,[])
    cur=[]
    for g in grp:
        if g in (0xFFFF,0xFFFE,0xFFD2):
            # treat line/page breaks as continuation (don't break run)
            continue
        if is_mapped(g) and g>1:  # skip squares(0)/spaces(1)
            cur.append(g)
        else:
            if len(cur)>len(best[2]):
                jp=sum(1 for x in cur if is_jp_glyph(x))
                best=(len(cur),jp,cur)
            cur=[]
    if len(cur)>len(best[2]):
        jp=sum(1 for x in cur if is_jp_glyph(x))
        best=(len(cur),jp,cur)
    return best

def romaji_safe(s):
    out=[]
    for ch in s:
        o=ord(ch)
        if 32<=o<127: out.append(ch)
        elif o==0x3000: out.append(' ')
        else: out.append('?')
    return re.sub(r"\s+"," ","".join(out)).strip()

def analyze(rid):
    p=os.path.join(RAW_DIR,f"{rid:04d}_type02.raw")
    data=open(p,"rb").read()
    sec2_size=struct.unpack_from("<I",data,0x14)[0]
    sec2_off=struct.unpack_from("<I",data,0x18)[0]
    if sec2_off==0 or sec2_off>=len(data) or sec2_size<4:
        return dict(rid=rid,kind="binary",groups=0,dlg=0,samples=[],note="no sec2",size=len(data))
    end=min(sec2_off+sec2_size,len(data)); sd=data[sec2_off:end]
    nw=len(sd)//2
    words=[struct.unpack_from(">H",sd,i*2)[0] for i in range(nw)]
    groups=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF: groups.append(words[start:i]); start=i+1
    if start<nw: groups.append(words[start:nw])

    dlg=[]
    for mi,grp in enumerate(groups):
        rl,jp,run=best_run(grp)
        # REAL dialogue: a contiguous mapped run of >=5 glyphs that contains >=2 JP chars,
        # and JP makes up a real fraction of the run (>=25%) => natural language, not coords.
        if rl>=5 and jp>=2 and (jp/rl)>=0.25:
            decoded="".join(gchar(g) for g in grp if g<0xFB00 or g in (0xFFFE,0xFFD2))
            dlg.append((mi,rl,jp,decoded))
    ngroups=len(groups)
    untrans=[m for m in dlg if (rid,m[0]) not in trans_msg]
    samples=[]
    for mi,rl,jp,dec in untrans[:5]:
        samples.append(dict(mi=mi,run=rl,jp=jp,gloss=romaji_safe(dec)[:140]))
    if not dlg:
        kind="binary"
    elif len(dlg)>=max(2,ngroups*0.10):
        kind="dialogue"
    else:
        kind="mixed"
    return dict(rid=rid,kind=kind,groups=ngroups,dlg=len(untrans),dlg_all=len(dlg),
               samples=samples,note=f"sec2={sec2_size}B",size=len(data))

raws=[]
for fn in os.listdir(RAW_DIR):
    if fn.endswith("_type02.raw"):
        rid=int(fn.split("_")[0])
        if 761<=rid<=911: raws.append(rid)
untrans_ids=sorted(r for r in raws if r not in trans_res)
results=[analyze(r) for r in untrans_ids]

with open(os.path.join(BASE,"build/_shard1_detail2.json"),"w",encoding="utf-8") as f:
    json.dump(results,f,ensure_ascii=False,indent=1)

from collections import Counter
lines=[]
lines.append("UNTRANS=%d kinds=%s"%(len(results),dict(Counter(x['kind'] for x in results))))
for x in results:
    lines.append("%4d %-8s groups=%4d dlg=%d dlgall=%d"%(x['rid'],x['kind'],x['groups'],x['dlg'],x['dlg_all']))
lines.append("=== SAMPLES ===")
for x in results:
    if x['samples']:
        lines.append("R%d %s dlg=%d:"%(x['rid'],x['kind'],x['dlg']))
        for s in x['samples'][:3]:
            lines.append("   M%d run=%d jp=%d | %s"%(s['mi'],s['run'],s['jp'],s['gloss']))
open(os.path.join(BASE,"build/_shard1_summary2.txt"),"w",encoding="utf-8").write("\n".join(lines))
print("done",len(results))
