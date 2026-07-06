"""Shard1 STRICT: real dialogue = a contiguous run of glyphs that ALL decode to
mapped chars (NO [XXXX] placeholders, NO float/binary markers), with JP density.
This separates true text from vertex/color/coordinate tables."""
import struct, json, os, re

BASE = "C:/Programmieren/wizardrytranslation"
RAW_DIR = os.path.join(BASE, "extracted/packdata_raw")
glyph_map = {int(k): v for k, v in json.load(open(os.path.join(BASE,"data/msg_glyph_map.json"),encoding="utf-8")).items()}
ovp=os.path.join(BASE,"data/type2_glyph_overrides.json")
if os.path.exists(ovp):
    for k,info in json.load(open(ovp,encoding="utf-8")).items(): glyph_map[int(k)]=info["t2"]
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
                    trans_msg.add((it["resource"],it["msg_index"]))

JP=re.compile(r"[぀-ゟ゠-ヿ㐀-鿿]")
PUNCT=re.compile(r"[、。「」『』！？・ー…　]")
def mapped(g): return (0<=g<=94) or (g in glyph_map)
def jpg(g):
    v=glyph_map.get(g); return bool(v) and (bool(JP.match(v)) or bool(PUNCT.match(v)))
def gchar(g):
    if g==0xFFFE: return " / "
    if g==0xFFD2: return " // "
    if 0<=g<=94: return chr(g+0x20)
    return glyph_map.get(g,f"[{g:04X}]")

def clean_runs(grp):
    """contiguous runs where every glyph is mapped (incl ascii) but NOT a hex placeholder.
    Spaces(1)/squares(0) and breaks allowed inside. Return list of (jp,total,glyphs)."""
    runs=[]; cur=[]
    for g in grp:
        if g in (0xFFFE,0xFFD2):
            continue
        if mapped(g):
            cur.append(g)
        else:
            if cur: runs.append(cur); cur=[]
    if cur: runs.append(cur)
    out=[]
    for r in runs:
        nonspace=[g for g in r if g>1]
        if not nonspace: continue
        jp=sum(1 for g in nonspace if jpg(g))
        out.append((jp,len(nonspace),r))
    return out

def safe(s):
    return re.sub(r"\s+"," ","".join(c if 32<=ord(c)<127 else ('?' if ord(c)>=0x80 else c) for c in s)).strip()

def analyze(rid):
    data=open(os.path.join(RAW_DIR,f"{rid:04d}_type02.raw"),"rb").read()
    sec2_size=struct.unpack_from("<I",data,0x14)[0]; sec2_off=struct.unpack_from("<I",data,0x18)[0]
    if sec2_off==0 or sec2_off>=len(data) or sec2_size<4:
        return dict(rid=rid,kind="binary",groups=0,dlg=0,samples=[],size=len(data),note="no sec2")
    end=min(sec2_off+sec2_size,len(data)); sd=data[sec2_off:end]; nw=len(sd)//2
    words=[struct.unpack_from(">H",sd,i*2)[0] for i in range(nw)]
    groups=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF: groups.append(words[start:i]); start=i+1
    if start<nw: groups.append(words[start:nw])
    dlg=[]
    for mi,grp in enumerate(groups):
        runs=clean_runs(grp)
        # STRICT real text: a clean run >=6 non-space glyphs with >=4 JP chars
        # AND JP fraction of that run >= 0.5  (true sentences are mostly JP)
        good=[r for r in runs if r[1]>=6 and r[0]>=4 and (r[0]/r[1])>=0.5]
        if good:
            decoded="".join(gchar(g) for g in grp if g<0xFB00 or g in (0xFFFE,0xFFD2))
            tot_jp=sum(r[0] for r in good)
            dlg.append((mi,tot_jp,decoded))
    untrans=[m for m in dlg if (rid,m[0]) not in trans_msg]
    samples=[dict(mi=m[0],jp=m[1],gloss=safe(m[2])[:160]) for m in untrans[:5]]
    if not dlg: kind="binary"
    elif len(dlg)>=max(2,len(groups)*0.10): kind="dialogue"
    else: kind="mixed"
    return dict(rid=rid,kind=kind,groups=len(groups),dlg=len(untrans),dlg_all=len(dlg),samples=samples,size=len(data),note=f"sec2={sec2_size}B")

raws=[int(fn.split("_")[0]) for fn in os.listdir(RAW_DIR) if fn.endswith("_type02.raw")]
ids=sorted(r for r in raws if 761<=r<=911 and r not in trans_res)
res=[analyze(r) for r in ids]
json.dump(res,open(os.path.join(BASE,"build/_shard1_detail3.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
from collections import Counter
L=["UNTRANS=%d kinds=%s"%(len(res),dict(Counter(x['kind'] for x in res)))]
for x in res: L.append("%4d %-8s groups=%4d dlg=%d dlgall=%d"%(x['rid'],x['kind'],x['groups'],x['dlg'],x['dlg_all']))
L.append("=== SAMPLES (strict clean-run text) ===")
for x in res:
    if x['samples']:
        L.append("R%d %s dlg=%d:"%(x['rid'],x['kind'],x['dlg']))
        for s in x['samples'][:4]: L.append("   M%d jp=%d | %s"%(s['mi'],s['jp'],s['gloss']))
open(os.path.join(BASE,"build/_shard1_summary3.txt"),"w",encoding="utf-8").write("\n".join(L))
print("done",len(res),dict(Counter(x['kind'] for x in res)))
