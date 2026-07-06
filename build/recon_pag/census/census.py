#!/usr/bin/env python3
"""Census of type-2 groups whose ENGLISH wrap (wrap=19, NO auto-PB) produces
any single PAGE with >4 on-screen lines.  Classifies each as dialogue vs
narration using a BLOCK-LEVEL discriminator derived from the Section-1 script:

  * Walk Section 1 (BFS) -> 0x04 DISPLAY_TEXT spans and 0x14 NAME/LABEL refs.
  * Each 0x04 block covers a contiguous run of Section-2 groups (off..off+cnt
    ends on a group's FFFF).  A block is DIALOGUE if ANY 0x14 label ref points
    into the block's group range OR the immediately-preceding group head
    (the name island sits at the head of the block's first group); else it is
    NARRATION.
  * A group's class = the class of the 0x04 block that displays it.  A group not
    covered by any walked 0x04 (rare) is classed by its own 0x14 presence, else
    UNKNOWN.

Also records: does the PRISTINE JP group/block use 0xFFD2 (native page break)?
"""
import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/Programmieren/wizardrytranslation'
os.chdir(ROOT)
sys.path.insert(0, 'tools')
sys.path.insert(0, 'build/recon_v89/phase2')

from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets, group_choice_markers, HEADER_SIZE
from verify_wrap import load_all_trans, load_pristine_choice_groups

# ---- replicate build_v9 Step-4 (current: wrap=19, NO auto-PB) ----
table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))
def enc(ch):
    if ch in table: return table[ch]
    if ch.lower() in table: return table[ch.lower()]
    return 31

TYPE2_WRAP_WIDTH = 19
def _wrap_line(seg, mx):
    out=[]
    while len(seg) > mx:
        brk = seg.rfind(' ', 0, mx+1)
        if brk <= 0: brk = mx
        out.append(seg[:brk]); seg = seg[brk:].lstrip(' ')
    out.append(seg); return out
def wrap_type2_text(text, mx=TYPE2_WRAP_WIDTH):
    pages=[]
    for page in text.split(' // '):
        lines=[]
        for seg in page.split(' / '):
            lines.extend(_wrap_line(seg, mx))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)

def pages_linecounts(en_text):
    """Return list of on-screen line counts, one entry per PAGE (split on ' // ')."""
    wrapped = wrap_type2_text(en_text)
    return [len(p.split(' / ')) for p in wrapped.split(' // ')]

# ---- load data ----
all_trans = load_all_trans()
manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
t02 = set()
for r in all_trans:
    if r < len(manifest) and not manifest[r].get('skipped') and manifest[r].get('type_code') == 2:
        t02.add(r)
t02.discard(1193)

RAW = 'extracted/packdata_raw'

def load_raw(r):
    p = f'{RAW}/{r:04d}_type02.raw'
    if not os.path.isfile(p): return None
    return open(p,'rb').read()

def build_block_classes(raw):
    """Return (group_class dict gi->('DIALOGUE'/'NARRATION'/'UNKNOWN'),
              group_jp_pb dict gi->bool jp 0xFFD2 in group,
              groups list, label_group_set, ok_walk)."""
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec1 = raw[0x20:sec2_off]
    sec2 = raw[sec2_off:sec2_off+sec2_size]
    groups, trailing = parse_sec2_group_offsets(sec2)
    nwords = len(sec2)//2
    words = [struct.unpack_from('>H', sec2, i*2)[0] for i in range(nwords)]
    # jp page-break per group
    jp_pb = {}
    for gi,(gs,ge) in enumerate(groups):
        jp_pb[gi] = any(words[w]==0xFFD2 for w in range(gs,ge))
    ok, instrs = walk(sec1)
    recs = extract_records(sec1, instrs)
    # which groups are name-label targets (0x14 off points into group head region)
    label_groups = set()
    for L in recs['label']:
        off = L['off']
        # find group containing off
        for gi,(gs,ge) in enumerate(groups):
            if gs <= off <= ge:
                label_groups.add(gi); break
    # build 0x04 blocks -> covered group ranges
    gclass = {}
    for D in recs['display']:
        off = D['off']; cnt = D['cnt']
        if cnt == 0: continue
        end = off + cnt  # exclusive-ish; span ends on a FFFF
        covered = [gi for gi,(gs,ge) in enumerate(groups) if not (ge < off or gs >= end)]
        if not covered: continue
        first = covered[0]
        # block is dialogue if any covered group OR the group preceding the
        # first covered group carries a 0x14 name island
        is_dialogue = any(gi in label_groups for gi in covered) or (first in label_groups) or ((first-1) in label_groups and first-1>=0)
        cls = 'DIALOGUE' if is_dialogue else 'NARRATION'
        for gi in covered:
            # don't downgrade an already-dialogue group to narration
            if gclass.get(gi) == 'DIALOGUE':
                continue
            gclass[gi] = cls
    return gclass, jp_pb, groups, label_groups, ok

# ---- main census ----
census = []  # (r, gi, page_counts, worst_page, cls, jp_pb_group, is_label_group, walk_ok)
walk_fail = []
for r in sorted(t02):
    raw = load_raw(r)
    if raw is None: continue
    choice = load_pristine_choice_groups(r)
    try:
        gclass, jp_pb, groups, label_groups, ok = build_block_classes(raw)
    except Exception as ex:
        gclass, jp_pb, groups, label_groups, ok = {}, {}, [], set(), False
    if not ok:
        walk_fail.append(r)
    for mi, en in all_trans[r].items():
        if mi in choice:
            continue  # choice groups are not wrapped/paginated
        pc = pages_linecounts(en)
        worst = max(pc) if pc else 0
        if worst > 4:
            cls = gclass.get(mi, 'UNKNOWN')
            census.append((r, mi, pc, worst, cls, jp_pb.get(mi, False),
                           mi in label_groups, ok))

# ---- report ----
print(f"Type-02 resources scanned: {len(t02)}   walk-failed: {len(walk_fail)} {sorted(walk_fail)[:20]}")
print(f"Total overflowing groups (any page >4 lines): {len(census)}\n")

from collections import Counter
cls_count = Counter(c[4] for c in census)
print("By class:", dict(cls_count))

# dialogue subset
dia = [c for c in census if c[4]=='DIALOGUE']
nar = [c for c in census if c[4]=='NARRATION']
unk = [c for c in census if c[4]=='UNKNOWN']
print(f"  DIALOGUE (need fix): {len(dia)}")
print(f"  NARRATION (must NOT touch): {len(nar)}")
print(f"  UNKNOWN: {len(unk)}")

# JP native pagebreak among dialogue
dia_jp = sum(1 for c in dia if c[5])
print(f"  of dialogue: JP group already has 0xFFD2: {dia_jp}")

print("\n=== WORST OFFENDERS (top 25 by worst-page line count) ===")
for c in sorted(census, key=lambda x:-x[3])[:25]:
    r,gi,pc,worst,cls,jppb,islbl,ok = c
    print(f"  R{r} g{gi}: pages={pc} worst={worst} [{cls}] jp_pb={jppb} label_grp={islbl} walk_ok={ok}")

print("\n=== UNKNOWN / ambiguous groups (full list) ===")
for c in unk:
    r,gi,pc,worst,cls,jppb,islbl,ok = c
    print(f"  R{r} g{gi}: pages={pc} worst={worst} jp_pb={jppb} label_grp={islbl} walk_ok={ok} EN={all_trans[r][gi][:70]!r}")

print("\n=== NARRATION overflowing groups (must NOT paginate) full list ===")
for c in sorted(nar, key=lambda x:-x[3]):
    r,gi,pc,worst,cls,jppb,islbl,ok = c
    print(f"  R{r} g{gi}: pages={pc} worst={worst} jp_pb={jppb} EN={all_trans[r][gi][:70]!r}")

# save full census
out = []
for c in census:
    r,gi,pc,worst,cls,jppb,islbl,ok = c
    out.append(dict(r=r,gi=gi,pages=pc,worst=worst,cls=cls,jp_pb=jppb,label_grp=islbl,walk_ok=ok,en=all_trans[r][gi]))
json.dump(out, open('build/recon_pag/census/census.json','w',encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"\nfull census -> build/recon_pag/census/census.json ({len(out)} rows)")
