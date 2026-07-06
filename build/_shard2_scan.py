"""SHARD 2 scoping scan: untranslated type-02 resources below R680.
Less-aggressive scan to catch sparse dialogue. ASCII summary to stdout,
JP samples to a UTF-8 file. Scoping only -- does not edit data."""
import struct, json, glob, os, re, sys

BASE = "C:/Programmieren/wizardrytranslation"
RAW_DIR = os.path.join(BASE, "extracted/packdata_raw")
GLYPH_MAP_PATH = os.path.join(BASE, "data/msg_glyph_map.json")
OVERRIDES_PATH = os.path.join(BASE, "data/type2_glyph_overrides.json")
OUT_JP = os.path.join(BASE, "build", "_shard2_jp_samples.txt")
OUT_JSON = os.path.join(BASE, "build", "_shard2_inventory.json")

with open(GLYPH_MAP_PATH, encoding="utf-8") as f:
    glyph_map = {int(k): v for k, v in json.load(f).items()}
if os.path.exists(OVERRIDES_PATH):
    with open(OVERRIDES_PATH, encoding="utf-8") as f:
        for gid, info in json.load(f).items():
            glyph_map[int(gid)] = info["t2"]

UNTRANS = [27,28,29,30,31,32,51,134,136,145,151,155,156,165,167,183,231,240,
241,245,307,308,311,314,315,319,322,325,326,332,333,338,342,393,402,403,408,
412,413,415,416,420,422,427,428,434,435,439,442,443,444,445,447,449,453,457,
465,467,471,473,474,500,502,503,507,508,509,512,514,515,530,531,558,584,588,
599,600,603,675,679]

CJK = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")
HIRA_KANJI = re.compile(r"[぀-ゟ一-鿿]")

def decode_glyph(g):
    if g == 0xFFFE: return " / "
    if g == 0xFFD2: return " // "
    if 0 <= g <= 94: return chr(g + 0x20)
    if g in glyph_map: return glyph_map[g]
    return None  # unmapped

def romaji_gloss(text):
    # crude ASCII-only gloss: keep ASCII, replace CJK with '#', collapse
    out = []
    for ch in text:
        o = ord(ch)
        if 32 <= o < 127:
            out.append(ch)
        elif ch in (" / ", "/"):
            out.append("/")
        else:
            out.append("#")
    s = "".join(out)
    s = re.sub(r"#+", lambda m: "#" + str(len(m.group(0))), s)
    return s[:80]

def analyze_group(glyphs):
    """Return (n_cjk, n_ascii_letter, max_run, zero_ratio, decoded_text).
    max_run = longest contiguous run of mapped text glyphs (CJK or ascii letter,
    not spaces/zeros). zero_ratio = fraction of words that are 0x0000."""
    parts = []
    n_cjk = 0
    n_ascii_letter = 0
    n_zero = 0
    cur_run = 0
    max_run = 0
    for g in glyphs:
        if g == 0:
            n_zero += 1
        if g >= 0xFB00 and g not in (0xFFFE, 0xFFD2):
            cur_run = 0
            continue  # control
        d = decode_glyph(g)
        if d is None:
            parts.append("�")  # unmapped marker
            cur_run = 0
            continue
        if d in (" / ", " // "):
            parts.append(d)
            cur_run = 0
            continue
        is_textchar = False
        for ch in d:
            if CJK.match(ch):
                n_cjk += 1
                is_textchar = True
            elif ch.isalpha():
                n_ascii_letter += 1
                is_textchar = True
        if is_textchar:
            cur_run += 1
            max_run = max(max_run, cur_run)
        else:
            cur_run = 0
        parts.append(d)
    text = "".join(parts)
    zr = n_zero / max(1, len(glyphs))
    return n_cjk, n_ascii_letter, max_run, zr, text

def scan(res):
    fn = os.path.join(RAW_DIR, f"{res:04d}_type02.raw")
    if not os.path.exists(fn):
        return {"resource": res, "kind": "undecodable", "dialogueMsgCount": 0,
                "notes": "raw file missing"}
    data = open(fn, "rb").read()
    if len(data) < 0x1C:
        return {"resource": res, "kind": "undecodable", "dialogueMsgCount": 0,
                "notes": "file < 0x1C"}
    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec2_off = struct.unpack_from("<I", data, 0x18)[0]
    if sec2_off == 0 or sec2_off >= len(data) or sec2_size < 4:
        return {"resource": res, "kind": "binary", "dialogueMsgCount": 0,
                "notes": f"no/empty sec2 (off={sec2_off},size={sec2_size}), file={len(data)}"}
    end = min(sec2_off + sec2_size, len(data))
    sec2 = data[sec2_off:end]
    n = len(sec2)//2
    words = [struct.unpack_from(">H", sec2, i*2)[0] for i in range(n)]
    groups = []
    start = 0
    for i in range(n):
        if words[i] == 0xFFFF:
            groups.append(words[start:i]); start = i+1
    if start < n:
        groups.append(words[start:])

    dialogue_count = 0
    cjk_groups = 0
    total_cjk = 0
    samples = []
    for gi, g in enumerate(groups):
        if not g:
            continue
        n_cjk, n_lat, max_run, zr, text = analyze_group(g)
        # LOOSE-but-real dialogue detection. Real glyph-stream dialogue has a
        # low zero-word ratio AND a contiguous run of mapped text glyphs.
        # Binary data tables have ~70%+ zero words and no real text runs.
        if zr > 0.5:
            continue  # binary data table, not a glyph stream
        is_dlg = (n_cjk >= 2 and max_run >= 2) or (n_cjk == 0 and n_lat >= 5 and max_run >= 4)
        if n_cjk >= 1:
            cjk_groups += 1
            total_cjk += n_cjk
        if is_dlg:
            dialogue_count += 1
            if len(samples) < 4 and (n_cjk >= 2):
                samples.append((res, gi, text, romaji_gloss(text)))
    nz = sum(1 for g in groups if g)

    # classify
    if dialogue_count == 0:
        kind = "binary"
        notes = f"{len(groups)} groups, {nz} nonempty, 0 dialogue, cjk_groups={cjk_groups}"
    elif dialogue_count >= max(3, nz*0.3):
        kind = "dialogue"
        notes = f"{len(groups)} groups, {nz} nonempty, {dialogue_count} dialogue, totalCJK={total_cjk}"
    else:
        kind = "mixed"
        notes = f"{len(groups)} groups, {nz} nonempty, {dialogue_count} dialogue (sparse), totalCJK={total_cjk}"
    return {"resource": res, "kind": kind, "dialogueMsgCount": dialogue_count,
            "notes": notes, "_samples": samples,
            "sample": samples[0][3] if samples else ""}

results = []
jp_lines = []
for res in UNTRANS:
    r = scan(res)
    samples = r.pop("_samples", [])
    results.append(r)
    if samples:
        jp_lines.append(f"\n===== R{res} ({r['kind']}, {r['dialogueMsgCount']} dialogue groups) =====")
        for (rs, gi, text, gloss) in samples:
            jp_lines.append(f"  R{rs}:G{gi} | {text[:120]}")

with open(OUT_JP, "w", encoding="utf-8") as f:
    f.write("SHARD 2 JP samples (untranslated type-02 below R680)\n")
    f.write("\n".join(jp_lines))
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1)

# ASCII summary to stdout
for r in results:
    print(f"R{r['resource']:>4} {r['kind']:>11} dlg={r['dialogueMsgCount']:>4}  {r['notes']}")
print("\nKIND TOTALS:")
from collections import Counter
c = Counter(r["kind"] for r in results)
for k,v in c.items(): print(f"  {k}: {v}")
print("total dialogue groups:", sum(r["dialogueMsgCount"] for r in results))
