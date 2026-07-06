#!/usr/bin/env python3
"""LOCATE: enumerate name/label entries lacking a name_labels.json mapping.

Scans:
  1) all type-02 resources' 0x14 NAME/LABEL slices (speaker nameplates / role
     names) -> decode via msg_glyph_map.json -> JP string. Untranslated = string
     with NO key in name_labels.json.
  2) R1892 (type20) roster name fields (LE katakana name-value runs).
  3) R2654 sub-7 roster name entries (BE katakana name-value runs).

Writes UTF-8 JSON report (no JP to stdout; ASCII summary only).
"""
import json, os, struct, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sec1_disasm as S

RAW = os.path.join(ROOT, "extracted", "packdata_raw")
GLYPH_MAP = json.load(open(os.path.join(ROOT, "data", "msg_glyph_map.json"), encoding="utf-8"))
NAME_LABELS = json.load(open(os.path.join(ROOT, "data", "name_labels.json"), encoding="utf-8"))
NL = {k: v for k, v in NAME_LABELS.items() if not k.startswith("_")}

OUT = os.path.join(ROOT, "build", "_untranslated_names_report.json")


def romaji_gloss(s):
    """ASCII-only gloss of a JP string for stdout/report safety."""
    return s.encode("ascii", "backslashreplace").decode("ascii")


def decode_slice(sec2, off_word, cnt):
    """Decode cnt glyph words starting at absolute word index off_word."""
    out = []
    n = len(sec2) // 2
    for i in range(off_word, off_word + cnt):
        if i < 0 or i >= n:
            return None
        g = struct.unpack_from(">H", sec2, i * 2)[0]
        if g >= 0xFB00 or g == 0xFFFF:
            return None
        ch = GLYPH_MAP.get(str(g))
        if ch is None:
            return None
        out.append(ch)
    return "".join(out)


# ---- 1) type-02 0x14 labels ----
label_hits = {}      # jp string -> {count, resources:set, kind}
label_undecodable = 0
res_scanned = 0
res_failed = 0
for path in sorted(glob.glob(os.path.join(RAW, "*_type02.raw"))):
    rid = os.path.basename(path).split("_")[0].lstrip("0") or "0"
    data = open(path, "rb").read()
    try:
        ok, instrs, sec1, sec2_off = S.walk_resource(data)
    except Exception:
        res_failed += 1
        continue
    if not ok:
        res_failed += 1
        # still try extract_records on partial walk
    res_scanned += 1
    sec2 = data[sec2_off:]
    try:
        recs = S.extract_records(sec1, instrs)
    except Exception:
        continue
    for r in recs["label"]:
        s = decode_slice(sec2, r["off"], r["cnt"])
        if s is None:
            label_undecodable += 1
            continue
        if not s.strip():
            continue
        if s in NL:
            continue
        e = label_hits.setdefault(s, {"count": 0, "resources": set()})
        e["count"] += 1
        e["resources"].add("R" + rid)

# ---- R1892 / R2654 katakana decode ----
KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA = {93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',
              246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv_to_kana(nv):
    if 193 <= nv <= 193+44: return KATA[nv-193]
    return KATA_EXTRA.get(nv, '〓')

r1892_unmapped = []
raw = open(os.path.join(RAW, "1892_type20.raw"), "rb").read()
REC_BASE, REC_STRIDE = 0x140, 0x130
n = (len(raw) - REC_BASE)//REC_STRIDE
for i in range(n):
    rs = REC_BASE + i*REC_STRIDE
    rid = struct.unpack_from('<H', raw, rs)[0]
    o = rs+2; vals=[]
    while o < rs+REC_STRIDE:
        v = struct.unpack_from('<H', raw, o)[0]
        if v==0xFFFF: break
        vals.append(v); o+=2
    if rid==0 or not vals: continue
    kana=''.join(nv_to_kana(v) for v in vals)
    if kana not in NL:
        r1892_unmapped.append({"rec":i,"id":rid,"kana":kana})

r2654_unmapped = []
raw = open(os.path.join(RAW, "2654_type44.raw"), "rb").read()
hdr=[dict(zip(('sub','size','off','z'), struct.unpack_from('<4I', raw, i*16))) for i in range(44)]
nh=next(h for h in hdr if h['sub']==7)
cnt=struct.unpack_from('>H', raw, nh['off'])[0]
offs=[struct.unpack_from('>H', raw, nh['off']+4+k*4)[0] for k in range(cnt)]
for k in range(cnt):
    st=nh['off']+offs[k]; en=nh['off']+(offs[k+1] if k+1<cnt else nh['size'])
    seg=raw[st:en]
    vals=[struct.unpack_from('>H', seg, p)[0] for p in range(0,len(seg)-1,2)]
    vals=[w for w in vals if w not in (0xFFFE,0xFFFF)]
    kana=''.join(nv_to_kana(v) for v in vals)
    if not kana: continue
    if kana not in NL:
        r2654_unmapped.append({"entry":k,"kana":kana})

report = {
    "type02_scanned": res_scanned, "type02_failed_walk": res_failed,
    "label_undecodable": label_undecodable,
    "labels_unmapped": [
        {"jp": k, "gloss": romaji_gloss(k), "count": v["count"],
         "resources": sorted(v["resources"])}
        for k, v in sorted(label_hits.items(), key=lambda x:-x[1]["count"])
    ],
    "r1892_unmapped": [{**d, "gloss": romaji_gloss(d["kana"])} for d in r1892_unmapped],
    "r2654_unmapped": [{**d, "gloss": romaji_gloss(d["kana"])} for d in r2654_unmapped],
}
json.dump(report, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("type02 scanned=%d failed_walk=%d undecodable_slices=%d" %
      (res_scanned, res_failed, label_undecodable))
print("unmapped distinct labels=%d" % len(label_hits))
print("r1892 unmapped=%d  r2654 unmapped=%d" % (len(r1892_unmapped), len(r2654_unmapped)))
print("report -> " + OUT)
# stdout ASCII glosses
for L in report["labels_unmapped"]:
    print("  LABEL x%-3d %-8s  %s" % (L["count"], ",".join(L["resources"][:4]), L["gloss"]))
