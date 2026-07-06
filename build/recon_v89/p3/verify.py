import sys, os, json, struct, glob, re
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.abspath("."))
sys.path.insert(0, os.path.abspath("tools"))
from patch_section1_offsets import inject_and_patch, group_choice_markers, parse_sec2_group_offsets, HEADER_SIZE

# replicate enc + table
table = json.load(open("data/english_glyph_table.json", encoding="utf-8"))
def enc(ch):
    if ch in table: return table[ch]
    if ch.lower() in table: return table[ch.lower()]
    return 31

# replicate wrap_type2_text (TYPE2_WRAP_WIDTH) -- read from build_v9 source
src = open("build/build_v9.py", encoding="utf-8").read()
m = re.search(r"TYPE2_WRAP_WIDTH\s*=\s*(\d+)", src)
WRAP = int(m.group(1)) if m else 18
def word_wrap(text, max_chars):
    segs = text.split(' / '); out=[]
    for seg in segs:
        while len(seg) > max_chars:
            brk = seg.rfind(' ', 0, max_chars+1)
            if brk <= 0: brk = max_chars
            out.append(seg[:brk]); seg = seg[brk:].lstrip(' ')
        out.append(seg)
    return ' / '.join(out)
def wrap_type2_text(text, max_chars=WRAP):
    # mirror: also split on ' // ' page boundaries
    pages = text.split(' // ')
    return ' // '.join(word_wrap(p, max_chars) for p in pages)

# load batch translations for R1197 only (same filter as build)
all_trans = {}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    d = json.load(open(fn, encoding='utf-8'))
    for e in d:
        if e.get('resource') != 1197: continue
        mi = e.get('msg_index'); en = e.get('english','')
        if mi is None: continue
        if not en: continue
        if any(ord(c) > 127 for c in en): continue
        all_trans[mi] = en

# choice groups
def load_choice(r_id):
    raw=open(f'extracted/packdata_raw/{r_id:04d}_type02.raw','rb').read()
    s2size=struct.unpack_from("<I",raw,0x14)[0]; s2off=struct.unpack_from("<I",raw,0x18)[0]
    sec2=raw[s2off:s2off+s2size]; n=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(n)]
    choice=set(); gi=0; start=0
    for i in range(n):
        if words[i]==0xFFFF:
            if group_choice_markers(words[start:i]): choice.add(gi)
            gi+=1; start=i+1
    return choice
choice_groups = load_choice(1197)

encoded={}
for mi,en_text in all_trans.items():
    if mi not in choice_groups:
        en_text = wrap_type2_text(en_text)
    glyphs=[]
    for page_i,page in enumerate(en_text.split(' // ')):
        if page_i>0: glyphs.append(0xFFD2)
        lc=0
        for pi,part in enumerate(page.split(' / ')):
            if pi>0:
                lc+=1
                if lc>=3: glyphs.append(0xFFD2); lc=0
                else: glyphs.append(0xFFFE)
            for ch in part: glyphs.append(enc(ch))
    encoded[mi]=glyphs

outdir="build/recon_v89/p3/out"
os.makedirs(outdir, exist_ok=True)
name,status = inject_and_patch(1197, encoded, 'extracted/packdata_raw', outdir)
print("inject:", name, status)

# decode g917 and g63 from output
gmap=json.load(open("data/msg_glyph_map.json",encoding="utf-8"))
erev={}
for ch,g in table.items(): erev.setdefault(g,ch)
def gly(w):
    if w>=0xFB00: return "<%04X>"%w
    if str(w) in gmap: return gmap[str(w)]
    if w in erev: return erev[w]
    return "[%d]"%w
raw=open(os.path.join(outdir,name),'rb').read()
s2size=struct.unpack_from("<I",raw,0x14)[0]; s2off=struct.unpack_from("<I",raw,0x18)[0]
sec2=raw[s2off:s2off+s2size]; groups,_=parse_sec2_group_offsets(sec2)
n=len(sec2)//2; words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(n)]
for gi in (63,917):
    a,b=groups[gi]; g=words[a:b]
    print("\nFIXED g%d HEX: %s" % (gi, " ".join("%04X"%w for w in g)))
    print("FIXED g%d TXT: %s" % (gi, "".join(gly(w) for w in g)))
    print("  choice markers:", [hex(w) for w in group_choice_markers(g)])

# verify_patched: re-walk for structural validity
from patch_section1_offsets import verify_patched
issues,t,nm = verify_patched('extracted/packdata_raw/1197_type02.raw', os.path.join(outdir,name))
print("\nverify_patched: display=%d name=%d issues=%d" % (t,nm,len(issues)))
for i in issues[:10]: print("  ISSUE:", i)
