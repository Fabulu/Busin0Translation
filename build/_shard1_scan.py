"""Shard 1 scoping scan: R761-R911 untranslated type-02 resources.
Less-aggressive than tools/extract_untranslated_type2.py.
Writes UTF-8 detail file; prints ASCII summary."""
import struct, json, os, re, sys

BASE = "C:/Programmieren/wizardrytranslation"
RAW_DIR = os.path.join(BASE, "extracted/packdata_raw")

glyph_map = {int(k): v for k, v in json.load(open(os.path.join(BASE,"data/msg_glyph_map.json"),encoding="utf-8")).items()}
ovp = os.path.join(BASE,"data/type2_glyph_overrides.json")
if os.path.exists(ovp):
    for k,info in json.load(open(ovp,encoding="utf-8")).items():
        glyph_map[int(k)] = info["t2"]

# translated resource ids
trans_res=set(); trans_msg=set()
import glob
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

JP_RE = re.compile(r"[぀-ヿ㐀-鿿　-〿＀-￯]")

def decode_glyph(g):
    if g==0xFFFE: return " / "
    if g==0xFFD2: return " // "
    if 0<=g<=94: return chr(g+0x20)
    if g in glyph_map: return glyph_map[g]
    return f"[{g:04X}]"

def romaji_safe(s):
    # produce ascii gloss: keep ascii, replace JP with '?'
    out=[]
    for ch in s:
        o=ord(ch)
        if 32<=o<127: out.append(ch)
        elif o in (0x3000,): out.append(' ')
        else: out.append('?')
    r="".join(out)
    return re.sub(r"\s+"," ",r).strip()

def classify_group(glyphs):
    """Return (kind, n_text_glyphs, n_jp, n_mapped, decoded) for a single FFFF group."""
    text=[g for g in glyphs if g<0xFB00 and g not in (0xFFFE,0xFFD2)]
    if not text: return None
    mapped=sum(1 for g in text if g<=94 or g in glyph_map)
    decoded="".join(decode_glyph(g) for g in glyphs if g<0xFB00)
    jp=len(JP_RE.findall(decoded))
    return (len(text), mapped, jp, decoded)

def analyze(rid):
    p=os.path.join(RAW_DIR,f"{rid:04d}_type02.raw")
    data=open(p,"rb").read()
    if len(data)<0x1C: return dict(rid=rid,kind="undecodable",groups=0,dlg=0,samples=[],note="too small",size=len(data))
    sec2_size=struct.unpack_from("<I",data,0x14)[0]
    sec2_off=struct.unpack_from("<I",data,0x18)[0]
    if sec2_off==0 or sec2_off>=len(data) or sec2_size<4:
        return dict(rid=rid,kind="binary",groups=0,dlg=0,samples=[],note="no/invalid sec2",size=len(data))
    end=min(sec2_off+sec2_size,len(data))
    sd=data[sec2_off:end]
    nw=len(sd)//2
    words=[struct.unpack_from(">H",sd,i*2)[0] for i in range(nw)]
    groups=[]; start=0
    for i in range(nw):
        if words[i]==0xFFFF:
            groups.append(words[start:i]); start=i+1
    if start<nw: groups.append(words[start:nw])

    dlg_msgs=[]   # (msg_idx, n_text, jp, decoded)
    for mi,grp in enumerate(groups):
        r=classify_group(grp)
        if r is None: continue
        ntext,mapped,jp,decoded=r
        # LESS aggressive: a group is "dialogue-ish" if it has any real JP run OR
        # a meaningful ascii word, with decent coverage.
        cov = mapped/ntext if ntext else 0
        # find longest run of consecutive mapped non-space glyphs
        run=0;maxrun=0
        for g in grp:
            if g<0xFB00 and g not in (0xFFFE,0xFFD2) and (g<=94 or g in glyph_map) and g>1:
                run+=1; maxrun=max(maxrun,run)
            else: run=0
        # dialogue if: at least 3 JP chars in a run-ish, or a 4+ run with >=40% coverage
        jp_run = bool(re.search(r"[぀-ヿ㐀-鿿]{2,}", decoded))
        is_dlg = False
        if ntext>=2 and cov>=0.4 and maxrun>=3 and (jp>=2 or jp_run):
            is_dlg=True
        # also catch very short but clearly-JP messages (1-3 glyphs all JP)
        elif ntext>=1 and jp>=ntext*0.8 and jp>=2:
            is_dlg=True
        if is_dlg:
            dlg_msgs.append((mi,ntext,jp,decoded))

    total_jp=sum(m[2] for m in dlg_msgs)
    ngroups=len(groups)
    ndlg=len(dlg_msgs)
    # how much of sec2 is text vs binary
    all_text=sum(1 for w in words if (w<=94 or w in glyph_map) and w not in (0xFFFF,))
    text_ratio = all_text/nw if nw else 0

    if ndlg==0:
        kind="binary"
    elif text_ratio>0.30 and ndlg>=ngroups*0.15:
        kind="dialogue"
    else:
        kind="mixed"

    # untranslated msg count: dlg msgs not already translated
    untrans = [m for m in dlg_msgs if (rid,m[0]) not in trans_msg]
    samples=[]
    for mi,ntext,jp,dec in untrans[:4]:
        samples.append(dict(mi=mi, jp=jp, gloss=romaji_safe(dec)[:120], dec=dec))
    return dict(rid=rid,kind=kind,groups=ngroups,dlg=len(untrans),dlg_all=ndlg,
                samples=samples,note=f"sec2={sec2_size}B text_ratio={text_ratio:.2f}",size=len(data))

# untranslated set
raws=[]
for fn in os.listdir(RAW_DIR):
    if fn.endswith("_type02.raw"):
        rid=int(fn.split("_")[0])
        if 761<=rid<=911: raws.append(rid)
untrans_ids=sorted(r for r in raws if r not in trans_res)

results=[analyze(r) for r in untrans_ids]

# write UTF-8 detail
with open(os.path.join(BASE,"build/_shard1_detail.json"),"w",encoding="utf-8") as f:
    json.dump(results,f,ensure_ascii=False,indent=1)

# ASCII summary to stdout
sys.stdout.reconfigure(encoding="utf-8")
from collections import Counter
kc=Counter(r["kind"] for r in results)
print("UNTRANSLATED in R761-911:",len(untrans_ids))
print("kinds:",dict(kc))
print("rid  kind     groups dlg  note")
for r in results:
    print(f"{r['rid']:4d} {r['kind']:9s} {r['groups']:5d} {r['dlg']:4d} {r['note']}")
print("---- DIALOGUE/MIXED samples (ascii gloss) ----")
for r in results:
    if r["kind"] in ("dialogue","mixed") and r["samples"]:
        print(f"R{r['rid']} ({r['kind']}, {r['dlg']} dlg groups):")
        for s in r["samples"][:2]:
            print(f"   M{s['mi']} jp={s['jp']}: {s['gloss']}")
