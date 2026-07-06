import struct, json, os, re, sys

BASE = "C:/Programmieren/wizardrytranslation"
RAW_DIR = os.path.join(BASE, "extracted/packdata_raw")
GLYPH_MAP_PATH = os.path.join(BASE, "data/msg_glyph_map.json")
OVERRIDES_PATH = os.path.join(BASE, "data/type2_glyph_overrides.json")

with open(GLYPH_MAP_PATH, encoding="utf-8") as f:
    glyph_map = {int(k): v for k, v in json.load(f).items()}
if os.path.exists(OVERRIDES_PATH):
    for gid_str, info in json.load(open(OVERRIDES_PATH, encoding="utf-8")).items():
        glyph_map[int(gid_str)] = info["t2"]

IDS = [912, 913, 914, 915, 916, 918, 922, 923, 924, 925, 926, 928, 930, 931, 1054, 1055, 1056, 1058, 1059, 1060, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 1070, 1071, 1074, 1076, 1078, 1079, 1080, 1082, 1085, 1086, 1087, 1088, 1089, 1090, 1092, 1094, 1095, 1096, 1100, 1103, 1106, 1107, 1108, 1116, 1117, 1118, 1120, 1124, 1126, 1127, 1128, 1132, 1134, 1137, 1142, 1148, 1152, 1154, 1156, 1157, 1158, 1159, 1162, 1187, 1189, 1192, 1195, 1214, 1358, 1359, 1360, 1361, 1362, 1363, 1365, 1366, 1367]

def decode_glyph(g):
    if g == 0xFFFE: return " / "
    if g == 0xFFD2: return " // "
    if 0 <= g <= 94: return chr(g + 0x20)
    if g in glyph_map: return glyph_map[g]
    return f"[{g:04X}]"

def decode_message(glyphs):
    out=[]
    for g in glyphs:
        if g >= 0xFB00 and g not in (0xFFFE,0xFFD2):
            continue
        out.append(decode_glyph(g))
    return "".join(out)

# romaji-ish ASCII gloss: strip JP, keep ASCII + mark unmapped
def ascii_gloss(text):
    # Replace any non-ASCII char with '.'
    out=[]
    for ch in text:
        o=ord(ch)
        if 32<=o<127: out.append(ch)
        else: out.append('.')
    s="".join(out)
    s=re.sub(r'\s+',' ',s).strip()
    return s[:80]

def classify_group(glyphs):
    # returns (is_dialogue, decoded_text, jp_char_count)
    text_glyphs=[g for g in glyphs if g<0xFB00 and g not in (0xFFFE,0xFFD2)]
    if not text_glyphs: return (False,"",0,0)
    mapped=[g for g in text_glyphs if g<=94 or g in glyph_map]
    if len(text_glyphs)==0: return (False,"",0,0)
    coverage=len(mapped)/len(text_glyphs)
    decoded=decode_message(glyphs)
    clean=re.sub(r'\[[0-9A-Fa-f]{4}\]','',decoded)
    # count japanese chars (hira/kana/kanji)
    jp=re.findall(r'[぀-ヿ一-鿿　-〿＀-￯]',clean)
    jpn=len(jp)
    # ascii letter runs (mapped ascii words)
    ascii_words=re.findall(r'[A-Za-z]{3,}',clean)
    # consecutive READABLE non-space character run, computed per-glyph on the
    # DECODED char. A glyph is "readable" if it decodes to a single real char
    # that is not whitespace and not a placeholder. Binary tables interleave
    # isolated mapped glyphs with 0x0 (space) cells -> runs stay at length 1.
    max_run=0;cur=0
    for g in text_glyphs:
        if g<=94:
            ch=chr(g+0x20)
        elif g in glyph_map:
            ch=glyph_map[g]
        else:
            ch=None  # unmapped/placeholder -> break
        if ch is not None and len(ch)==1 and not ch.isspace() and ch not in '　・':
            cur+=1; max_run=max(max_run,cur)
        else:
            cur=0
    # placeholder ratio: fraction of glyphs that are UNMAPPED (rendered as [XXXX])
    unmapped=len(text_glyphs)-len(mapped)
    ph_ratio=unmapped/len(text_glyphs) if text_glyphs else 1.0
    # detect binary fill-pattern: a single hex value dominating the unmapped glyphs
    # (e.g. 0x803F repeated structurally in data tables)
    from collections import Counter
    unmapped_vals=[g for g in text_glyphs if not (g<=94 or g in glyph_map)]
    dom=0
    if unmapped_vals:
        dom=Counter(unmapped_vals).most_common(1)[0][1]/len(unmapped_vals)
    # DIALOGUE decision (LESS aggressive but reject binary fill noise):
    is_dialogue=False
    # reject groups dominated by placeholders (binary), or by a single repeated fill value
    binary_fill = (ph_ratio>0.5) or (dom>0.4 and unmapped>20)
    # Build readable-run list for THIS group: split decoded char stream on
    # space/placeholder, keep runs of >=4 readable chars.
    rchars=[]
    for g in text_glyphs:
        if g<=94: ch=chr(g+0x20)
        elif g in glyph_map: ch=glyph_map[g]
        else: ch=None
        if ch is not None and len(ch)==1 and not ch.isspace() and ch not in '　・':
            rchars.append(ch)
        else:
            rchars.append('\x00')
    runs=[r for r in "".join(rchars).split('\x00') if len(r)>=4]
    # Binary record table signature: the readable content is one short pattern
    # repeated identically many times (e.g. coordinate tables, [803F] fills).
    repeated_pattern=False
    if runs:
        from collections import Counter as _C
        rc=_C(runs)
        top_run,top_n=rc.most_common(1)[0]
        # if a single short (<=8) run dominates and repeats 5+ times -> binary
        if len(top_run)<=8 and top_n>=5 and top_n>=len(runs)*0.5:
            repeated_pattern=True
    # longest run length
    longest=max((len(r) for r in runs), default=0)

    # require a real WORD/sentence: a readable run of >=8 chars, OR several
    # varied medium runs. Reject binary fills and repeated fixed patterns.
    is_dialogue=False
    if coverage>=0.55 and not binary_fill and not repeated_pattern:
        distinct_long=len({r for r in runs if len(r)>=4})
        if longest>=8 and (jpn>=2 or len(ascii_words)>=1 or re.search(r'[゠-ヿ]{3,}',clean)):
            is_dialogue=True
        elif longest>=5 and distinct_long>=3 and jpn>=3:
            # several varied real runs -> short sparse dialogue
            is_dialogue=True
    return (is_dialogue, decoded, jpn, len(text_glyphs))

results=[]
jp_out_lines=[]
for rid in IDS:
    path=os.path.join(RAW_DIR, f"{rid:04d}_type02.raw")
    if not os.path.exists(path):
        results.append((rid,"missing",0,0,0,[]))
        continue
    data=open(path,'rb').read()
    if len(data)<0x1C:
        results.append((rid,"undecodable",0,0,0,[]))
        continue
    sec2_size=struct.unpack_from("<I",data,0x14)[0]
    sec2_off=struct.unpack_from("<I",data,0x18)[0]
    if sec2_off==0 or sec2_off>=len(data) or sec2_size<4:
        results.append((rid,"binary",0,len(data),0,[]))
        continue
    sec2_end=min(sec2_off+sec2_size,len(data))
    sec2=data[sec2_off:sec2_end]
    nw=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(nw)]
    groups=[];start=0
    for i in range(nw):
        if words[i]==0xFFFF:
            groups.append(words[start:i]);start=i+1
    if start<nw:
        groups.append(words[start:nw])
    dlg_count=0
    total_jp=0
    samples=[]
    for gi,grp in enumerate(groups):
        if not grp: continue
        isd,decoded,jpn,tg=classify_group(grp)
        if isd:
            dlg_count+=1
            total_jp+=jpn
            if len(samples)<3:
                samples.append((gi,decoded))
    # classify resource
    if dlg_count==0:
        kind="binary"
    else:
        # mixed if there are many non-dialogue groups with substantial data, else dialogue
        nonempty=sum(1 for g in groups if g)
        if dlg_count>=1 and dlg_count < nonempty*0.5 and nonempty-dlg_count>5:
            kind="mixed"
        else:
            kind="dialogue"
    results.append((rid,kind,dlg_count,len(data),total_jp,samples))
    if samples:
        jp_out_lines.append(f"=== R{rid} ({kind}, {dlg_count} dialogue groups) ===")
        for gi,dec in samples:
            jp_out_lines.append(f"  [g{gi}] {dec}")
        jp_out_lines.append("")

# write JP samples to UTF-8
with open(os.path.join(BASE,"build","_shard3_jp_samples.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(jp_out_lines))

# ASCII summary to stdout
print(f"{'RID':>5} {'KIND':<11} {'DLG':>4} {'BYTES':>8} {'JPchars':>7}  SAMPLE")
out_json=[]
for rid,kind,dlg,nb,jpn,samples in results:
    samp=""
    if samples:
        samp=ascii_gloss(samples[0][1])
    print(f"{rid:>5} {kind:<11} {dlg:>4} {nb:>8} {jpn:>7}  {samp}")
    out_json.append({"resource":rid,"kind":kind,"dialogueMsgCount":dlg,"jp":jpn,"sample":samp})

json.dump(out_json, open(os.path.join(BASE,"build","_shard3_results.json"),"w"), indent=1)
# totals
print("\nTOTALS:")
from collections import Counter
c=Counter(r[1] for r in results)
print(dict(c))
print("untranslated scanned:", len(IDS))
