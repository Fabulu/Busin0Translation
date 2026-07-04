#!/usr/bin/env python3
"""Build v9 ISO: variable-size type-2 injection + Section 1 opcode patching"""
import sys, os, struct, json, glob, shutil, math

os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')

SECTOR = 2048

print("=" * 60)
print("  BUILD v9 - Full variable-size + Section 1 patching")
print("=" * 60)

# ===== STEP 1: Run v2 pipeline for type-1 resources =====
print("\n=== Step 1: Type-1 injection (v2 pipeline) ===")
rc = os.system('python build/build_full_english_v2.py')
if rc != 0:
    print('FATAL: Step 1 (build_full_english_v2.py) failed -- stale packdata_resources would ship')
    sys.exit(1)
print("  v2 pipeline complete")

# Remove unsafe type-03/06 resources that v2 pipeline incorrectly patches
for unsafe_r, tc in [(1053, '03'), (1908, '06')]:
    f = f'build/packdata_resources/{unsafe_r:04d}_type{tc}.raw'
    if os.path.exists(f):
        os.remove(f)
        print(f"  Removed unsafe R{unsafe_r} (type-{tc})")

# ===== STEP 2: Fix problem type-1 resources (R34, R35, R2124, R2654) =====
print("\n=== Step 2: Fix type-1 FFFF mismatches ===")
table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))

translations = {}
for i in range(10):
    try:
        d = json.load(open(f'data/translate_chunks/chunk_{i:02d}_translated.json', encoding='utf-8'))
        for e in d:
            k = (e.get('resource', -1), e.get('message', -1))
            en = e.get('english', '').strip()
            if en and en != e.get('japanese', ''):
                translations[k] = en
    except:
        pass
for fix in ['chunk_r38_fix.json', 'chunk_r43_fix.json', 'chunk_r37_extra.json', 'chunk_r40_r42_translated.json', 'chunk_r36_translated.json', 'chunk_r37_r48_r49_translated.json', 'chunk_r43_r45_translated.json', 'chunk_r35_menus_fix.json', 'chunk_r2654_library_fix.json']:
    try:
        d = json.load(open(f'data/translate_chunks/{fix}', encoding='utf-8'))
        for e in d:
            k = (e.get('resource', -1), e.get('message', -1))
            en = e.get('english', '').strip()
            if en:
                translations[k] = en
    except:
        pass

def enc(ch):
    if ch in table:
        return table[ch]
    if ch.lower() in table:
        return table[ch.lower()]
    return 31

def word_wrap(text, max_chars=18):
    """Wrap text to fit within max_chars per line.

    Preserves existing ' / ' line breaks.  For segments that exceed
    max_chars, inserts ' / ' at the last space before the limit.
    """
    segments = text.split(' / ')
    wrapped = []
    for seg in segments:
        while len(seg) > max_chars:
            # find last space at or before max_chars
            brk = seg.rfind(' ', 0, max_chars + 1)
            if brk <= 0:
                # no space found — force break at max_chars
                brk = max_chars
            wrapped.append(seg[:brk])
            seg = seg[brk:].lstrip(' ')
        wrapped.append(seg)
    return ' / '.join(wrapped)

for r_id in [34, 35, 2654]:  # In-place translation (NONE are truly flat: each needs its own data_start)
    tc_map = {34: '20', 35: '02', 2654: '44'}
    tc = tc_map.get(r_id, '01')
    orig = bytearray(open(f'extracted/packdata_raw/{r_id:04d}_type{tc}.raw', 'rb').read())
    rt = {m: e for (r, m), e in translations.items() if r == r_id}
    # R2654 (type-44) and R34 (type-20) have multi-section headers before
    # the glyph data. The glyph data offset is stored at header byte 8 (LE u32).
    # Scanning for FFFF from byte 0 would treat the header as group 0,
    # and writing translations there corrupts the header -> VIF FIFO crash.
    data_start = 0
    if r_id in (34, 2654):
        data_start = struct.unpack_from('<I', orig, 8)[0]
    elif r_id == 35:
        # R35 is NOT flat: it has a 0x20-byte type-02-style header (sec2_off
        # LE u32 = 0x230 at +0x18) followed at 0x20 by a 25-entry offset table
        # (BE u16 count 0x0019 + ascending BE u32s 0x68, 0x6E, ...) ending at
        # 0x86, where the first FFFF sits. Scanning from byte 0 made "group 0"
        # = header + offset table, and message 1 ('Save') was written over it
        # (the v85 QA bug: header destroyed, table zeroed). Text starts right
        # after the table. Layout + mapping verified empirically:
        # build/recon_v85/qa/r35_alignment_check.py
        data_start = 0x22 + 4 * struct.unpack_from('>H', orig, 0x20)[0]  # 0x86
    fp = [i for i in range(data_start, len(orig) - 1, 2) if struct.unpack_from('>H', orig, i)[0] == 0xFFFF]
    groups = []
    prev = data_start
    for f in fp:
        groups.append((prev, f + 2))
        prev = f + 2
    out = bytearray(orig)
    rep = 0
    for gi, (g_s, g_e) in enumerate(groups):
        if r_id == 34:
            # R34: group 0 is a STRUCTURAL TABLE (word[0]=49 count followed by
            # 49 ascending u16 values, zero-interleaved), NOT text — never write it.
            # Group 1 is empty; item-name text starts at group 2 = message 1.
            # Alignment verified empirically (build/recon_v85/font-artifacts/
            # r34_alignment_check.py): decoded Japanese of group gi matches the
            # chunk 'japanese' of message gi-1 for 24/25 entries exactly
            # (the 25th differs by one ambiguous glyph-map entry only).
            if gi == 0:
                continue
            mi = gi - 1
        elif r_id == 35:
            # R35: group 0 (scanned from data_start=0x86) is an EMPTY pre-text
            # group (lone FFFF at 0x86) — never write it. Text group gi maps
            # to message gi - 1. Alignment verified empirically
            # (build/recon_v85/qa/r35_alignment_check.py): decoded Japanese of
            # group gi matches the chunk 'japanese' of message gi-1 for 16/19
            # entries exactly (the other 3 differ only by '■' placeholder
            # glyphs in the chunk Japanese, not by alignment).
            if gi == 0:
                continue
            mi = gi - 1
        else:
            mi = gi + 1
        if mi not in rt:
            continue
        en = rt[mi]
        if any(ord(c) > 127 for c in en):
            continue
        ocs = g_e - g_s - 2
        ctrls = bytearray()
        p = g_s
        while p < g_e - 1:
            v = struct.unpack_from('>H', orig, p)[0]
            if v >= 0xFB00 and v not in (0xFFFF, 0xFFFE):
                ctrls += struct.pack('>H', v)
                p += 2
            else:
                break
        en = word_wrap(en)
        gls = []
        for pi, pt in enumerate(en.split(' / ')):
            if pi > 0:
                gls.append(0xFFFE)
            for c in pt:
                gls.append(enc(c))
        nc = ctrls
        for g in gls:
            nc += struct.pack('>H', g)
        padded = len(nc) < ocs
        while len(nc) < ocs:
            nc += struct.pack('>H', 0)
        if len(nc) > ocs:
            nc = nc[:ocs]
        # R2654 structural invariant (tests/test_v86_strips.test_R2654_structural):
        # every Format-A sub's string payload must end FFFE FFFF. The FFFF
        # terminator at out[g_e-2:g_e] is untouched; when our English is shorter
        # than the original budget the tail is 0x0000-padded, which would strand
        # the group ending as '0000 FFFF' (breaks the sub-final group of sub 29,
        # which is where the Library body records 1888-1894 live). Restoring a
        # trailing FFFE (line break) before the terminator matches the pristine
        # format — every original group ends in a line break — and is visually
        # harmless (a trailing blank line). Scoped to r_id==2654 only; R34/R35
        # have their own byte-identity guards below and must NOT be touched.
        if r_id == 2654 and padded and len(nc) >= 2:
            nc[-2:] = struct.pack('>H', 0xFFFE)
        out[g_s:g_e - 2] = nc
        rep += 1
    if r_id == 34:
        # Guard: the structural table group (group 0) must be byte-identical
        # to the original — a corrupted table breaks R34 item lookups.
        t_s, t_e = groups[0]
        assert bytes(out[t_s:t_e]) == bytes(orig[t_s:t_e]), \
            "R34 structural table (group 0) was modified — aborting build"
    if r_id == 35:
        # Guard: header + offset table + empty group 0 (bytes 0 .. first text
        # group start, 0x88) must be byte-identical to the original — writing
        # there is exactly the v85 'Save'-over-header corruption.
        first_text = groups[1][0] if len(groups) > 1 else data_start
        assert bytes(out[:first_text]) == bytes(orig[:first_text]), \
            "R35 header/offset table (bytes 0..first text group) was modified — aborting build"
    pd = (SECTOR - len(out) % SECTOR) % SECTOR
    out += b'\x00' * pd
    open(f'build/packdata_resources/{r_id:04d}_type{tc}.raw', 'wb').write(out)
    nf = sum(1 for i in range(0, len(out) - 1, 2) if struct.unpack_from('>H', out, i)[0] == 0xFFFF)
    status = 'OK' if len(fp) == nf else 'MISMATCH!'
    print(f"  R{r_id}: {rep} replaced, FFFF {len(fp)}=={nf} {status}")

# ===== STEP 3: R39 custom type-15 injection =====
print("\n=== Step 3: R39 type-15 injection ===")
if os.path.exists('build/packdata_resources/0039_type15.raw'):
    os.remove('build/packdata_resources/0039_type15.raw')
rc = os.system('python build/inject_r39_v2.py')
if rc != 0:
    print('FATAL: R39 injection failed: build/inject_r39_v2.py')
    sys.exit(1)
print("  R39 injected")

# ===== STEP 3.1: R39 inline Japanese glyph patching =====
print("\n=== Step 3.1: R39 inline Japanese patch ===")
rc = os.system('python tools/patch_r39_inline.py')
if rc != 0:
    print('FATAL: R39 inline patch failed: tools/patch_r39_inline.py')
    sys.exit(1)
print("  R39 inline labels patched")

# ===== STEP 3.2: R39 quest UI labels and quest titles =====
print("\n=== Step 3.2: R39 quest labels and titles ===")
rc = os.system('python build/inject_r39_quest.py')
if rc != 0:
    print('FATAL: R39 quest injection failed: build/inject_r39_quest.py')
    sys.exit(1)
print("  R39 quest labels injected")

# ===== STEP 3.3: R39 block-2 spell descriptions =====
# Size-changing block-2 rebuild (spell descriptions, off 3648). Runs AFTER the quest
# step so it composes with block0/quest edits; has its own PRISTINE-DIFF GATE asserting
# every byte outside block2 is unchanged. v159: ALL 56 records translated incl.
# g55/56/57 (Stigma/Raheal/Offset — the old "no source text" claim was an artifact
# of the misaligned pre-v159 enumeration).
print("\n=== Step 3.3: R39 block-2 spell descriptions ===")
rc = os.system('python tools/patch_r39_spell_desc.py')
if rc != 0:
    print('FATAL: R39 spell-desc injection failed: tools/patch_r39_spell_desc.py')
    sys.exit(1)
print("  R39 spell descriptions injected")

# ===== STEP 3.4: R39 AA names/descriptions/UI (blocks 3/4/5) =====
# v161: size-changing rebuild of block 3 (AA/technique names g11+, from the shipped
# R1361/R1362 strip names verbatim), block 4 (37 AA descriptions + 45 party
# requirements) and block 5 (AA-setup UI messages). Same gated pattern as Step 3.3
# (count-header offset-table rebuild, pristine-diff gate, header-driven offsets so
# it composes after the block-2 growth). Data: data/r39_aa_descriptions.json.
print("\n=== Step 3.4: R39 AA names/descriptions ===")
rc = os.system('python tools/patch_r39_aa.py')
if rc != 0:
    print('FATAL: R39 AA injection failed: tools/patch_r39_aa.py')
    sys.exit(1)
print("  R39 AA text injected")

# ===== STEP 3.5: R46/R47 type-03 injection =====
print("\n=== Step 3.5: R46/R47 type-03 injection ===")
rc = os.system('python build/inject_r46_r47.py')
if rc != 0:
    print('FATAL: Step 3.5 (inject_r46_r47.py) failed')
    sys.exit(1)
print("  R46/R47 injected")

# ===== STEP 3.6/3.7: R1188 patches DISABLED (BUG-3) =====
# R1188 is the LIVE dialogue/narration font: a 1024x1024 PSMT4 atlas of 24x24
# serif glyph cells DMA'd verbatim from disc to VRAM 0x3000 (proven via GS dump
# 20260612061701). The patchers below wrote 'name entry labels'/kana cells with
# layout assumptions off by 1008 bytes, scattering writes into ~150 live glyph
# cells (ASCII U,V,Z,[,r,x,y,z,~ and most kana) — the cause of the r/y/V glyph
# artifacts (BUG-3). The labels they wrote were never consumed: the companion
# EXE patch was never implemented, and tab labels already render English via
# R2138 sub7 (tools/patch_r2138.py, Step 3.9). R1188 must ship pristine.
print("\n=== Step 3.6/3.7: R1188 patches DISABLED (BUG-3: live dialogue font) ===")
# os.system('python tools/patch_r1188_comprehensive.py')
# os.system('python tools/patch_r1188_bw256.py')
# Delete any stale patched override so rebuild_packdata.py falls back to the
# pristine extracted/packdata_raw/1188_type01.raw.
_r1188_override = 'build/packdata_resources/1188_type01.raw'
if os.path.exists(_r1188_override):
    os.remove(_r1188_override)
    print("  Removed stale R1188 override — pristine 1188_type01.raw will be used")
else:
    print("  No R1188 override present — pristine 1188_type01.raw will be used")

# ===== STEP 3.8: R2100 chargen font atlas patch =====
print("\n=== Step 3.8: R2100 chargen font atlas ===")
rc = os.system('python tools/patch_r2100.py')
if rc != 0:
    print('FATAL: Step 3.8 (patch_r2100.py) failed')
    sys.exit(1)

# ===== STEP 3.9: R2138 unified patcher (all sub-resources) =====
print("\n=== Step 3.9: R2138 unified patcher (sub0/4/6/7/25/26/27) ===")
rc = os.system('python tools/patch_r2138.py')
if rc != 0:
    print('FATAL: Step 3.9 (patch_r2138.py) failed')
    sys.exit(1)

# ===== STEP 4: Variable-size type-2 injection + Section 1 patching =====
print("\n=== Step 4: Variable-size type-2 + Section 1 patching ===")

from patch_section1_offsets import inject_and_patch, group_choice_markers, HEADER_SIZE
from dialogue_classifier import (
    build_dialogue_map, build_narration_map, build_narration_pad_map)
import glyph_metrics  # SoT for per-glyph widths. NEVER recompute.

# Type-2 word-wrap width.  The BOXED dialogue frame fits ~20 cells (JP shipped
# 18-19 glyphs/line); centered NARRATION is authored at <=16.  v91 used 16 which
# wrapped boxed dialogue FAR too early (e.g. "That's why / you're / looking for")
# blowing 3-line dialogue up to 5 short lines that overflow the box.  Width 19
# matches the boxed frame (1-cell safety margin under ~20) AND is byte-identical
# for narration (its authored lines are already <=16, so _wrap_line is a no-op
# there).  This is the regression fix for v89 overflow (the loop previously never
# word-wrapped, so ~2604 lines clipped).  Width 20 (v98): Patch-12 (patch_exe.py)
# set the per-glyph dialogue X-advance to 18px, so more characters fit per line —
# width 20 packs boxed dialogue tighter (fewer wrapped lines -> less vertical
# overflow) while staying within the ~20-cell boxed frame.  Do NOT exceed 20
# without freshly re-measuring the box width and the centered-narration
# space-advance (25 was rejected as too aggressive).
TYPE2_WRAP_WIDTH = 20

# P3 box-budget raise (thing8-10 measurement).  The GS-mapped dialogue text-clip
# right edge in the thing8-10 dumps is ~376px; minus a ~4px safety margin = 372px.
# (The prior 324px ceiling — "handles requests for" = 324px at x=[51,375],
# data/spacing_baseline.md — was over-conservative: it left ~52px of the box
# unfilled, so long dialogue still ran >3 lines.)  372px cuts the share of
# dialogue groups wrapping >3 lines roughly in half (~4.0% -> ~2.0% of 2152
# BUDGET pinned by LIVE PLAYTEST (2026-06-22), overriding the earlier 588px recon
# estimate: barkeepfull g904 "I will be blunt. I cannot take on" = 454px rendered
# PERFECT/full-width, while lines at 470-473px ("but I'll strive...", "I must know.
# What befell Simzon's") spilled past the right edge (dialoguetoomuch / stillfucked).
# So the true box interior is ~455-465px.  456 keeps the 454px reference on one line
# and re-wraps the 470px+ overflows.  (Was 480 — too generous, the rare-overflow bug.)
DIALOGUE_BOX_PX = 456

# Narration budget — the box's usable width.
NARRATION_BOX_PX = 360


def pad_narration_left_align(text):
    """LEFT-ALIGN centered narration WITHOUT an EXE change, by exploiting the
    engine's own per-line CENTER-anchor (origin = boxCenter - glyphCount*12/2,
    count-based — confirmed from the boxX setters at EXE 0x305cd4 / 0x305c9c and
    the indent.ps2 fog capture).  If every line in a page has the SAME glyph count,
    they all centre identically -> their left edges line up -> the block reads as
    left-aligned.  So pad each line with TRAILING SPACES (0x0000 cells, blank but
    counted) up to the longest line on its page.  Pure data; the on-screen text is
    unchanged, only the invisible trailing pad differs.  (Still needs the small
    boxX reposition so the now-left-aligned block sits on-screen.)"""
    out_pages = []
    for page in text.split(' // '):
        lines = page.split(' / ')
        width = max(len(l) for l in lines)
        out_pages.append(' / '.join(l + ' ' * (width - len(l)) for l in lines))
    return ' // '.join(out_pages)


def _wrap_line(seg, max_chars):
    """Hard-wrap one ' / '-free segment into a list of <=max_chars lines.

    Breaks at spaces; only force-breaks mid-token when a single token alone
    exceeds max_chars (mirrors the Step-2 word_wrap helper)."""
    out = []
    while len(seg) > max_chars:
        brk = seg.rfind(' ', 0, max_chars + 1)
        if brk <= 0:
            brk = max_chars  # single oversize token -> force break
        out.append(seg[:brk])
        seg = seg[brk:].lstrip(' ')
    out.append(seg)
    return out


def wrap_type2_text(text, max_chars=TYPE2_WRAP_WIDTH):
    """Word-wrap a type-2 english string, PRESERVING its ' // ' page breaks and
    ' / ' line breaks and inserting additional ' / ' breaks only where a line
    segment exceeds max_chars.  Choice groups must NOT be passed here."""
    pages = []
    for page in text.split(' // '):
        lines = []
        for seg in page.split(' / '):
            lines.extend(_wrap_line(seg, max_chars))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)


def reflow_dialogue(text, width):
    """Re-flow a BOXED-DIALOGUE string to fewer lines (v98 vertical-overflow fix).

    Per ' // ' page, COLLAPSE the premature single-line ' / ' breaks (the JP
    author wrapped at the narrow JP cell pitch) back into one flat string, then
    re-wrap at `width` using the SAME greedy wrapper wrap_type2_text uses
    (_wrap_line).  ' // ' page boundaries are PRESERVED.  This relies on the
    18px Patch-12 X-advance to fit more glyphs per line, so collapsing + re-
    wrapping yields <= the original number of ' / ' breaks per page (verified).

    DIALOGUE-ONLY: the caller gates this behind build_dialogue_map so narration
    (and choice/structural groups) are never reflowed."""
    pages = []
    for page in text.split(' // '):
        flat = ' '.join(s.strip() for s in page.split(' / ') if s.strip())
        pages.append(' / '.join(_wrap_line(flat, width)))
    return ' // '.join(pages)


def _wrap_line_px(seg, box_px):
    """Greedy word-wrap one ' / '-free segment into a list of lines, each with
    glyph_metrics.px_width <= box_px (T4 px-budget wrap).

    Widths come EXCLUSIVELY from the shared SoT glyph_metrics.px_width(seg, enc)
    using build_v9's own enc (char-32 family) — NEVER a local recompute.  A single
    oversize token (already wider than box_px on its own) is emitted on its own
    line rather than split mid-token: far better than the v89 100-glyph run, and
    real translations rarely contain such a token."""
    words = seg.split(' ')
    lines, cur = [], ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if cur and glyph_metrics.px_width(cand, enc) > box_px:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines or ['']


def wrap_px(text, box_px=DIALOGUE_BOX_PX, collapse=True):
    """Pixel-budget re-wrap a BOXED-DIALOGUE string (T4).  Replaces the char-count
    reflow_dialogue + wrap_type2_text on the dialogue path: per ' // ' page,
    COLLAPSE the premature ' / ' breaks (the JP author wrapped at the narrow JP
    cell pitch) into one flat string, then re-wrap at `box_px` pixels.  ' // '
    page boundaries are PRESERVED.

    Break-agnostic: only ' / ' (line) / ' // ' (page) markers in and out — the
    downstream encoder turns each into a single 0xFFFE word and NEVER emits
    0xFFD2 (the v97 colour-code rule).  DIALOGUE-ONLY: the caller gates this behind
    build_dialogue_map so narration/choice/structural groups are untouched."""
    if collapse:
        # Collapse ACROSS ' // ' too (v97: ' // ' is a line-break 0xFFFE, NOT a page
        # break), so a short tail after a ' // ' (e.g. the orphaned 'it."') is not
        # stranded on its own line.  Flatten the WHOLE string, then re-wrap at box_px.
        flat = ' '.join(s.strip() for s in text.replace(' // ', ' / ').split(' / ') if s.strip())
        return ' / '.join(_wrap_line_px(flat, box_px))
    # collapse=False: preserve ' // ' page boundaries, only re-wrap within each ' / '.
    pages = []
    for page in text.split(' // '):
        lines = []
        for seg in page.split(' / '):
            lines.extend(_wrap_line_px(seg, box_px))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)


# R1203 Section-2 ceiling (v142): the old 65,535-word cap was a SELF-IMPOSED
# u16 myth.  VERIFIED in tools/sec1_disasm.py: Section 1 references Section 2
# ONLY via u32 word offsets/counts -- opcode 0x04 off=beu32@+2 cnt=beu32@+6,
# opcode 0x14 off=beu32@+6 cnt=beu32@+10 (extract_records, lines 152-167); the
# patcher writes them back as ">I" (patch_section1, struct.pack_into ">I" at
# pc+2/+6/+10) and the header sec2-size at 0x14 is "<I" (32-bit).  The only u16
# fields are the 0x0C/0x0D name_ref *group indices* (idx@+4), which count FFFF
# groups (max 1632) -- NOT word offsets.  Pristine R1203 already references word
# offset 50204 (76% of the old cap), and a full inject of all 1580 translations
# lands at 77,065 words -- all offsets stay u32-clean.  The REAL ceiling is u32
# (4,294,967,295 words).  Lifting this admits the ~718 previously-dropped
# dungeon groups (incl. the NPC menu g1115 + dialogue 1116-1144).
# derive_r1203_cap() below is retained ONLY as a safety clamp against the u32
# ceiling -- with this limit it never trims a real group.
# To REVERT to the conservative cap, set this back to 65535.
R1203_S2_LIMIT = 0xFFFFFFFF  # u32 word ceiling (was 65535 -- the u16 myth)


def derive_r1203_cap(encoded_trans, raw_dir, out_dir):
    """RE-DERIVE the highest R1203 group index whose REAL injected Section-2 word
    count stays <= R1203_S2_LIMIT, under the CURRENT (already px-encoded,
    0xFFFE-only) encoding.

    No stale constant: the cap is found by binary-searching the actual
    inject_and_patch output (header 0x14 = Section-2 BYTES; //2 = words), which
    is authoritative because it includes name-island English-label expansion.
    The pre-v97 recon helper (verify_wrap.encode_msg) is deliberately NOT reused —
    it emits 0xFFD2 — so the encoded dict handed in here (built by the build loop)
    is the only input.

    Returns the cap group index (an integer key from encoded_trans)."""
    keys = sorted(encoded_trans)
    if not keys:
        return 0

    def words_at(cap):
        capped = {mi: g for mi, g in encoded_trans.items() if mi <= cap}
        res = inject_and_patch(1203, capped, raw_dir, out_dir)
        if res[0] is None:
            return None
        out = open(os.path.join(out_dir, res[0]), 'rb').read()
        return struct.unpack_from('<I', out, 0x14)[0] // 2

    lo, hi, best = 0, len(keys) - 1, keys[0]
    while lo <= hi:
        mid = (lo + hi) // 2
        w = words_at(keys[mid])
        if w is not None and w <= R1203_S2_LIMIT:
            best = keys[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


# NOTE (v97): the v96 boxed-dialogue auto-pagination was REVERTED.  It inserted a
# 0xFFD2 ' // ' "page break" every BOX_CAPACITY lines — but 0xFFD2 is NOT a page
# break in this engine: it is an inline TEXT-COLOR control code (the 0xFFD0-0xFFD9
# family, handlers 0x303370-0x303430; 0xFFD2 = set color-state 3).  The boxed
# renderer's draw loop (VA 0x307510 @0x307904) skips every word >= 0x8000 and the
# layout pass (0x302DB0) records a line ONLY on 0xFFFE — so the injected 0xFFD2
# did nothing for layout (dialogue still overflowed) AND silently changed text
# color, and a stray 0xFFD2/0xFFFE in the flat R1197 menu-label group softlocked
# the request menu.  The engine paginates ONLY by splitting content across
# separate scene-script groups (a future group-split, not an in-stream word).
# Auto-pagination is therefore removed; long dialogue is left as v91 produced it.


def load_pristine_choice_groups(res_idx, raw_dir='extracted/packdata_raw'):
    """Return the set of group indices in the pristine type-02 resource whose
    FFFF-group carries a choice marker (0xFFC0..0xFFCF).  These message indices
    must be encoded WITHOUT word-wrapping so encode_choice_group's segment->option
    mapping stays intact.  Returns an empty set if the raw is missing/unparsable."""
    path = f'{raw_dir}/{res_idx:04d}_type02.raw'
    if not os.path.isfile(path):
        return set()
    try:
        raw = open(path, 'rb').read()
        if len(raw) < HEADER_SIZE:
            return set()
        sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
        sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
        if sec2_off < HEADER_SIZE or sec2_off >= len(raw) or sec2_size < 4:
            return set()
        sec2 = raw[sec2_off:sec2_off + sec2_size]
        n_words = len(sec2) // 2
        words = [struct.unpack_from('>H', sec2, i * 2)[0] for i in range(n_words)]
        choice = set()
        gi = 0
        start = 0
        for i in range(n_words):
            if words[i] == 0xFFFF:
                if group_choice_markers(words[start:i]):
                    choice.add(gi)
                gi += 1
                start = i + 1
        return choice
    except Exception:
        return set()

# Structural FLAT-RUN groups that must SHIP PRISTINE (NOT translated): their
# labels are addressed by an offset table / menu dispatch and have ZERO in-stream
# 0xFFFE separators, so wrapping or breaking them desyncs the dispatch.  R1197
# msg_index 1 is the Bar Luna Light request-menu label list — our breaks caused
# the request-menu SOFTLOCK (render-verified: requestbroken__ee.bin).  Until a
# proper offset-table-aware menu-label injector exists, ship these pristine.
SKIP_STRUCTURAL_GROUPS = {(1197, 1)}

# DIALOGUE-WRAP EXCLUSIONS (P3 false-positive guard).  These 6 (resource,
# msg_index) groups are CLASSIFIER false-positives: build_dialogue_map flags them
# as boxed dialogue, but they are intentional ' / '/literal-newline LISTS whose
# line structure is load-bearing — collapsing + re-wrapping them (wrap_px) would
# flatten the list into a paragraph and risk an R1197-class menu/structure
# corruption (softlock).  They must bypass BOTH wrap_px paths (dialogue AND
# narration) and ship with their authored break structure intact:
#   R1194 g0   — the ending crawl (multi-line authored passage)
#   R1196 g810 — a literal-newline menu list
#   R1200 g64  — short-segment list
#   R1212 g1   — short-segment list
#   R1213 g1   — short-segment list
#   R1353 g1   — short-segment list
# Unlike SKIP_STRUCTURAL_GROUPS these are still TRANSLATED (they keep their
# English + authored ' / ' breaks) — they are only excluded from the px re-wrap.
DIALOGUE_WRAP_EXCLUDE = {(1194, 0), (1196, 810), (1200, 64),
                         (1212, 1), (1213, 1), (1353, 1)}

# NARRATION-PAD EXCLUSIONS (W1-NARR).  build_narration_pad_map() exposes the
# mode-N name-island narration bodies that the classifier drops at line 159 so
# they can receive the left-align pad (the tavern-intro R1197 g2 class).  Its
# body-span predicate already rejects nameplate-dense menu lists (e.g. R1203 g1
# / R1204 g14 / R1210 g1, the "Explore / Master? / Storage 1-10 ..." list groups
# whose every line is its own 0x14 label record).  These extra (resource,
# msg_index) groups are menu/list structures that the engine composes from
# per-line cells and MUST ship pristine (padding them risks the R1197-class
# request-menu softlock).  They are excluded from the pad-only branch as a
# belt-and-suspenders guard on top of the body-span predicate.
NARR_PAD_EXCLUDE = {(1197, 1), (1212, 1), (1213, 1), (1353, 1)}

# BOX-MODE MECHANISM (2026-06-20): render mode is now read DIRECTLY from the
# engine's own rule in tools/dialogue_classifier.py — every 0x04 DISPLAY block is
# preceded (control-flow order) by a 0x12 GOSUB to a mode-config helper whose first
# 0x63 align opcode carries the mode (op0==0 DIALOGUE, >=1 NARRATION), grounded in
# the EXE write 0x2FA520 -> ctx+0x2a7 -> renderer branch 0x307E48.  Validated 19/19
# on ground truth incl. the cutscene cases (barkeep g4 inherited nameplate; the
# g7/g13/g926/g575 narration interludes that share a dialogue window — which defeat
# every heuristic).  build_dialogue_map / build_narration_map are now an exact
# partition of every covered group, so the old manual DIALOGUE_FORCE override is
# GONE — the classifier reproduces the box mode for all ~8455 dialogue / ~4289
# narration groups corpus-wide with no hand-curation (data/dialogue_force.json is
# obsolete).  Only 4 long dialogue groups (R1209) need an authored ' // ' page split.

# Load ALL type-2 translations
all_trans = {}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        d = json.load(open(fn, encoding='utf-8'))
        for e in d:
            r = e['resource']
            mi = e['msg_index']
            if (r, mi) in SKIP_STRUCTURAL_GROUPS:
                continue
            en = e.get('english', '')
            if not en:
                continue
            if en.startswith('[DATA]') or en.startswith('[LAYOUT]') or en.startswith('[BINARY]'):
                continue
            if en.startswith('[MAP]') or en.startswith('[SYSTEM]') or en.startswith('[GLYPH'):
                continue
            if en.startswith('[DEBUG]'):
                continue
            if any(ord(c) > 127 for c in en):
                continue
            if r not in all_trans:
                all_trans[r] = {}
            all_trans[r][mi] = en
    except Exception as ex:
        print(f"  Warning: {fn}: {ex}")

print(f"  Loaded translations for {len(all_trans)} resources")

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
type02_resources = set()
for r in all_trans:
    if r < len(manifest) and not manifest[r].get('skipped') and manifest[r].get('type_code') == 2:
        type02_resources.add(r)

# Exclude R1193 -- handled manually in Step 5 (has trailing data without FFFF terminator)
type02_resources.discard(1193)

print(f"  Type-02 dialogue resources: {len(type02_resources)}")

os.makedirs('build/patched_type2', exist_ok=True)

# Purge stale artifacts from previous builds: the Section-1 patcher SKIPS
# resources whose Section 1 fails to walk, so a leftover *.raw from an older
# (corrupted) run would otherwise survive and be merged in Step 6.
_stale = glob.glob('build/patched_type2/*.raw')
for _f in _stale:
    os.remove(_f)
print(f"  Purged {len(_stale)} stale files from build/patched_type2")

total_patched = 0
total_encoded = 0

for r_id in sorted(type02_resources):
    msg_trans = all_trans[r_id]

    # Choice groups (pristine FFC0..FFCF) must skip word-wrapping so the
    # downstream encode_choice_group segment->option mapping stays byte-exact.
    choice_groups = load_pristine_choice_groups(r_id)

    # Boxed-dialogue groups (v98): only these may be REFLOWED (collapse premature
    # ' / ' breaks then re-wrap) to reduce vertical overflow.  build_dialogue_map
    # errs toward NARRATION (zero narration->dialogue false positives), so any
    # group NOT in this set is byte-identical to before (reflow skipped).  An
    # unwalkable Section 1 yields an empty set -> nothing reflowed (ships as v97).
    dialogue_groups = build_dialogue_map(r_id)

    # Bare-DISPLAY centered-narration groups (P1): the INVERSE of the dialogue
    # classifier — a single 0x04 DISPLAY block NOT headed by a 0x14 name-island.
    # These are re-wrapped at NARRATION_BOX_PX (collapse=True) to widen the far-
    # too-narrow JP-pitch line breaks.  Structural/menu/list groups are NOT bare
    # single-DISPLAY groups, so they are excluded and ship byte-identical to v97.
    # Unwalkable Section 1 -> empty set (ship pristine).
    narration_groups = build_narration_map(r_id)

    # Name-island narration bodies (W1-NARR): mode-N groups that carry a small
    # 0x14 label island at their head and are therefore DROPPED from
    # build_narration_map by the classifier's line-159 nameplate skip.  Without
    # this they fall to the un-padded wrap_type2_text else-branch and render
    # center-anchored/ragged (the tavern-intro R1197 g2 bug).  build_narration_pad_map
    # returns only the groups whose non-label body span is substantial (so dense
    # menu/list groups like R1203 g1 are NOT included); we route these through the
    # IDENTICAL wrap_px(collapse)+pad path as the narration branch.  The D/N
    # partition is unchanged, so the classifier's 19/19 ground truth is preserved.
    narration_pad_groups = build_narration_pad_map(r_id)

    # Encode English text to glyph lists
    encoded_trans = {}
    # msg_indices that received pad_narration_left_align (equal-count trailing pad).
    # The engine left-aligns these ONLY when every line carries the SAME counted
    # length.  inject_and_patch re-attaches the pristine group's trailing control
    # words AFTER our text -- and a trailing COLOUR-state code (0xFFD0-0xFFD9) lands
    # on the last line, inflating ONLY that line's engine-counted length (descriptor
    # lc array @desc+0x40) above the padded glyph count, so the last line re-centres
    # narrower and the block reads ragged/centered (R1198 g24 "...go to the
    # labyrinth?": live lc=[25,28]).  We hand these indices to inject_and_patch so it
    # DROPS a trailing colour-control on exactly these groups (a colour-SET right
    # before the FFFF terminator governs no following glyph, so removing it is
    # visually inert).  Dialogue groups are NEVER in this set, so their trailing
    # controls (all 0xFFE0, never 0xFFD0-9) are untouched.
    leftalign_pad_groups = set()
    for mi, en_text in msg_trans.items():
        # Word-wrap dialogue/narration so no on-screen line exceeds the frame
        # width (the v89 overflow fix).  Choice-group questions+options are
        # passed through unchanged — wrapping them would corrupt the option
        # segmentation in encode_choice_group.
        if (r_id, mi) in DIALOGUE_WRAP_EXCLUDE:
            # P3 false-positive guard: classifier mis-flags these as dialogue but
            # they are intentional ' / '/literal-newline LISTS.  Bypass BOTH wrap_px
            # paths AND the char-wrapper so their authored break structure ships
            # byte-identical (the encoded glyph list is unchanged from pristine).
            pass
        elif mi not in choice_groups:
            # Wrap ONLY boxed dialogue at the GS-measured 372px pixel budget (P3):
            # collapse premature ' / ' breaks within each ' // ' page, then re-wrap
            # to <=372px lines via the shared glyph_metrics px widths.  This packs
            # more glyphs/line than the char-20 path (=> fewer 0xFFFE => less
            # vertical overflow AND a smaller Section 2).  Narration/structural
            # groups are NOT in dialogue_groups, so they pass straight to
            # wrap_type2_text byte-identically to v97 — the gate is dialogue-only.
            if mi in dialogue_groups:
                # Engine-classified BOXED DIALOGUE (the 0x63-helper rule): wrap at
                # the wide 480px box, collapsing premature ' / ' breaks.
                en_text = wrap_px(en_text, DIALOGUE_BOX_PX)
            elif mi in narration_groups:
                en_text = wrap_px(en_text, NARRATION_BOX_PX, collapse=True)
                # LEFT-ALIGN: pad every line to equal glyph count so the engine's
                # count-based per-line centering (lc array @desc+0x40, recomputed each
                # frame from the text) aligns all left edges.  Trailing pad is blank.
                en_text = pad_narration_left_align(en_text)
                leftalign_pad_groups.add(mi)
            elif mi in narration_pad_groups and (r_id, mi) not in NARR_PAD_EXCLUDE:
                # W1-NARR: name-island narration body dropped from build_narration_map
                # by the classifier's nameplate skip.  Route it through the IDENTICAL
                # path as the narration branch so its left edges align (the engine
                # draws the 0x14 name-island as a SEPARATE nameplate, so padding the
                # body lines does not disturb it).
                en_text = wrap_px(en_text, NARRATION_BOX_PX, collapse=True)
                en_text = pad_narration_left_align(en_text)
                leftalign_pad_groups.add(mi)
            else:
                en_text = wrap_type2_text(en_text)
        # Translations use " / " and " // " as LINE breaks -> 0xFFFE.  We NEVER
        # emit 0xFFD2: it is NOT a page break in this engine (it is an inline
        # text-COLOR control code, 0xFFD0-0xFFD9 family — see the v97 note above),
        # so a " // " is treated identically to a " / " (a line break).  This
        # means long dialogue still overflows the box (true pagination needs a
        # scene-script group split, deferred), but it never corrupts text color
        # or softlocks a menu.  Both break types are one u16 word, so the R1203
        # cap below is unchanged.
        glyphs = []
        parts = [seg for page in en_text.split(' // ') for seg in page.split(' / ')]
        for pi, part in enumerate(parts):
            if pi > 0:
                glyphs.append(0xFFFE)  # line break (from " / " or " // ")
            for ch in part:
                glyphs.append(enc(ch))
        encoded_trans[mi] = glyphs

    # R1203: Section 2 overflow guard.
    # The English translation grows Section 2 past the u16 limit of 65,535 words.
    # The total must account for ALL groups (translated + original), because every
    # group still occupies space even if untranslated.
    # The cap is RE-DERIVED dynamically from the REAL injected Section-2 word count
    # of the ALREADY-px-encoded, 0xFFFE-only dict (derive_r1203_cap) — NO stale
    # constant.  The T4 px-wrap packs more glyphs per line => fewer 0xFFFE => a
    # SMALLER Section 2 => the cap can only rise vs the old char-wrap literal
    # (1016).  encoded_trans already reflects the px-wrap because the encoding loop
    # above ran wrap_px before this block.
    if r_id == 1203:
        _tmp = 'build/_r1203_cap_tmp'
        os.makedirs(_tmp, exist_ok=True)
        R1203_MAX_GROUP = derive_r1203_cap(
            encoded_trans, 'extracted/packdata_raw', _tmp)
        before = len(encoded_trans)
        encoded_trans = {mi: g for mi, g in encoded_trans.items() if mi <= R1203_MAX_GROUP}
        print(
            "  R1203: re-derived cap group %d (px-wrap), dropped %d overflow translations"
            % (R1203_MAX_GROUP, before - len(encoded_trans))
        )

    result = inject_and_patch(
        r_id, encoded_trans,
        'extracted/packdata_raw',
        'build/patched_type2',
        strip_trailing_color_groups=leftalign_pad_groups
    )

    if result[0]:
        total_patched += 1
        total_encoded += len(encoded_trans)
        print(f"  R{r_id}: {result[1]}")
    else:
        print(f"  R{r_id}: SKIPPED -- {result[1]}")

print(f"  Patched {total_patched} resources, {total_encoded} messages")

# ===== STEP 5: R1193 intro narration injection =====
# R1193's boot prologue (BUG-10) lives in a TRAILING block after the last FFFF
# group terminator, drawn line-by-line by 23 Section-1 0x14 records.
# tools/patch_r1193_narration.py injects the FFFF-group translations via
# inject_and_patch (group-0 narration islands preserved, patch_section1 runs
# inside), rebuilds the trailing block as 23 English lines (pages 4/3/2/4/1/
# 3/2/3/1, <= 23 glyphs each) and rewrites each 0x14 record's WORD_OFF/
# GLYPH_CNT exactly. Writes build/patched_type2/1193_type02.raw.
print("\n=== Step 5: R1193 intro narration ===")
if 1193 in all_trans and os.path.exists('extracted/packdata_raw/1193_type02.raw'):
    from patch_r1193_narration import build_r1193
    build_r1193('extracted/packdata_raw/1193_type02.raw', all_trans[1193],
                'build/patched_type2')
else:
    # Fallback: copy existing file
    if os.path.exists('build/packdata_resources/1193_type02.raw'):
        shutil.copy('build/packdata_resources/1193_type02.raw', 'build/patched_type2/1193_type02.raw')
        print("  R1193 preserved (no translation found)")

# ===== STEP 5c: R1194 ending narration + R1193 short-prologue variant =====
# v161: R1194's ENDING narration is drawn by 42 Section-1 0x14 line records that
# the Step-4 name-island preservation kept as verbatim JP (the 0x04 body was
# English, the line records were not). tools/patch_r1194_narration.py rebuilds
# group 0 as [42 EN lines][EN tail][FFFF], rewrites every record's WORD_OFF/
# GLYPH_CNT, and re-points the 0x04 at the tail — same gate battery as the
# R1193 patcher. fix_r1193_short_prologue() additionally covers R1193's second,
# 10-record "short prologue" variant (walk-proven reachable) by appending its
# English lines at the END of Section 2 (zero existing offsets move).
print("\n=== Step 5c: R1194 ending narration ===")
if 1194 in all_trans and os.path.exists('extracted/packdata_raw/1194_type02.raw'):
    from patch_r1194_narration import build_r1194, fix_r1193_short_prologue
    build_r1194('extracted/packdata_raw/1194_type02.raw', all_trans[1194],
                'build/patched_type2')
    if os.path.exists('build/patched_type2/1193_type02.raw'):
        fix_r1193_short_prologue('build/patched_type2')
    print("  R1194 ending narration + R1193 short-prologue injected")
else:
    print("  R1194 SKIPPED (no translation/pristine found)")

# ===== STEP 6: Merge and clean =====
print("\n=== Step 6: Merge resources ===")
for f in os.listdir('build/patched_type2'):
    shutil.copy(f'build/patched_type2/{f}', f'build/packdata_resources/{f}')


def _scan_jp_residue(all_trans, raw_dir='extracted/packdata_raw',
                     out_dir='build/patched_type2'):
    """Post-inject JP-RESIDUE guard (v142).

    For every type-02 resource that has at least one non-empty batch
    translation, compare each FFFF-group's Section-2 bytes in the PATCHED output
    against the PRISTINE raw.  Any group that (a) still byte-matches pristine JP
    while (b) having a non-empty translation in all_trans is REPORTED as residue
    -- it shipped Japanese despite a translation existing.  This catches both the
    R1203 word-cap drops and any choice/structural group the encoder bailed on.

    This is a LOUD WARNING, NOT a hard build failure: other capped/structural
    groups may legitimately remain pristine for now, and we want the FULL residue
    scope visible in one report rather than stopping at the first one.

    Returns the list of (res, group) residue tuples."""
    def _groups(data):
        if len(data) < 0x20:
            return None
        sec2_size = struct.unpack_from('<I', data, 0x14)[0]
        sec2_off = struct.unpack_from('<I', data, 0x18)[0]
        if sec2_off < 0x20 or sec2_off + sec2_size > len(data):
            return None
        sec2 = data[sec2_off:sec2_off + sec2_size]
        groups = []
        start = 0
        i = 0
        n = len(sec2)
        # split on big-endian 0xFFFF group terminators (word-aligned)
        while i + 1 < n:
            if sec2[i] == 0xFF and sec2[i + 1] == 0xFF:
                groups.append(sec2[start:i])
                start = i + 2
                i += 2
            else:
                i += 2
        return groups

    residue = []
    for r in sorted(all_trans):
        # only type-02 resources we actually inject through Step 4 produce a
        # patched_type2 output; resources patched elsewhere (or shipped pristine)
        # have no out file -> skip (their text path is not the Section-2 inject).
        out_path = os.path.join(out_dir, f'{r:04d}_type02.raw')
        raw_path = os.path.join(raw_dir, f'{r:04d}_type02.raw')
        if not (os.path.isfile(out_path) and os.path.isfile(raw_path)):
            continue
        try:
            og = _groups(open(out_path, 'rb').read())
            pg = _groups(open(raw_path, 'rb').read())
        except Exception:
            continue
        if og is None or pg is None:
            continue
        for mi, en in all_trans[r].items():
            if not en or not isinstance(mi, int):
                continue
            if mi >= len(og) or mi >= len(pg):
                continue
            if og[mi] == pg[mi]:
                residue.append((r, mi))
    return residue


print("\n=== Step 6.1: JP-residue guard (v142) ===")
_residue = _scan_jp_residue(all_trans)
if _residue:
    # group by resource for a compact report
    _by_res = {}
    for r, mi in _residue:
        _by_res.setdefault(r, []).append(mi)
    print("  WARNING: %d translated group(s) still ship PRISTINE JAPANESE:"
          % len(_residue))
    for r in sorted(_by_res):
        gl = sorted(_by_res[r])
        if len(gl) <= 20:
            _gs = ','.join(str(g) for g in gl)
        else:
            _gs = '%s,...,%s (%d groups)' % (
                ','.join(str(g) for g in gl[:10]),
                gl[-1], len(gl))
        print("    R%d: groups %s" % (r, _gs))
else:
    print("  OK: no JP residue -- every translated group differs from pristine.")

# Skip-fallback: any type-02 resource the Section-1 patcher SKIPPED this run
# has no file in build/patched_type2 — remove any stale override in
# build/packdata_resources so rebuild_packdata falls back to the pristine raw.
# (Only ids from type02_resources + 1193. R35 is EXCLUDED: although it has
# type_code 2 and appears in type02_resources, build/packdata_resources/
# 0035_type02.raw is written by Step 2 each run and must never be deleted here.)
for _rid in sorted((type02_resources | {1193}) - {35}):
    _name = f'{_rid:04d}_type02.raw'
    if not os.path.exists(f'build/patched_type2/{_name}'):
        _stale_out = f'build/packdata_resources/{_name}'
        if os.path.exists(_stale_out):
            os.remove(_stale_out)
            print(f"  R{_rid} skipped this run — removed stale override {_name} (ships pristine)")

binary_resources = [677,690,712,715,726,741,750,757,769,780,785,787,793,795,797,799,
    801,803,816,837,839,852,860,862,864,866,868,870,871,873,875,877,879,881,883,885,
    889,917,920,1057,1061,1072,1073,1077,1084,1091,1093,1099,1105,1109,1110,1112,
    1123,1133,1141,1145,1146,1147,1174,1192,1912,1930,1931,1933,1934,1935,1936,
    1939,1940,1941,1948,1952,1953,1959,1972,2141,2144,2161,2162,2163,2166,2174,
    2176,2200,2201,2204,2206,2207,2208,2588,2589,2651,2652,2653]
for r in binary_resources:
    f = f'build/packdata_resources/{r:04d}_type02.raw'
    if os.path.exists(f):
        os.remove(f)

file_count = len(os.listdir('build/packdata_resources'))
print(f"  {file_count} files in build/packdata_resources")

# ===== Step 6.5: v86 pre-rendered UI strips + item DB =====
# Runs AFTER Step 6's stale-override purge and binary_resources deletion loop,
# and BEFORE Step 7's PACKDATA rebuild. This placement is CRITICAL and safe:
#   - The Step 6 binary_resources loop deletes 2141/2144 (and other *_type02.raw
#     names) BEFORE this block, so facility/strip outputs written here survive to
#     Step 7. If this block ran before that loop, 2141_type02/2144_type02 would be
#     deleted out from under us.
#   - Several outputs here use *_type02.raw names (1359/1360/1361/1362/1363/1365/
#     1367/1910/1054). Even though some of those ids may appear in type02_resources
#     or binary_resources, BOTH the Step 6 stale-override purge and the
#     binary_resources deletion loop have already run by this point — nothing
#     between here and Step 7 deletes any *.raw — so these outputs ship intact.
#   - inject_r34_db.py reads build/packdata_resources/2654_type44.raw (Step 2's
#     output, carrying co-op sub0 translations) as its R2654 base and overwrites
#     0034_type20.raw + 2654_type44.raw. Neither the stale-override purge nor the
#     binary_resources loop touch those names (both operate on *_type02.raw only;
#     R2654 is type44, R0034 is type20), so the Step 2 base survives to here.
print("\n=== Step 6.5: v86 pre-rendered UI strips + item DB ===")
for script in [
    'tools/patch_r2124.py',
    'tools/patch_r1365.py',
    'tools/patch_battle_strips.py',
    'tools/patch_camp_strips.py',
    'tools/patch_facility_strips.py',
    'tools/patch_r2147.py',
    'tools/patch_r1370.py',
    'tools/patch_r2880.py',
    'tools/patch_r2881_ending.py',
    'tools/patch_r2882_grave.py',
    'build/inject_r34_db.py',
    'tools/patch_r2654_names.py',  # romanize party-bar roster names (AFTER inject_r34_db, reads its R2654 output)
    'tools/patch_r2654_library.py',  # v163: variable-length LIBRARY name subs (monster/spell/AA names; AFTER the two above -- composes on their R2654 output)
    'tools/patch_r1892_names.py',  # romanize the REAL party-bar name source R1892 (LE roster; R2654 is off the bar's path)
]:
    rc = os.system(f'python {script}')
    if rc != 0:
        print(f'FATAL: v86 patcher failed: {script}')
        sys.exit(1)

# --- DIAGNOSTIC: ship R39 PRISTINE to test the request-menu regression hypothesis ---
# When build/R39_PRISTINE.flag exists, drop our patched R39 so rebuild_packdata
# falls back to extracted/packdata_raw/0039_type15.raw (the original).  Isolates
# whether our R39 quest injection (risky offset-table rebuild) breaks the request menu.
if os.path.exists('build/R39_PRISTINE.flag'):
    if os.path.exists('build/packdata_resources/0039_type15.raw'):
        os.remove('build/packdata_resources/0039_type15.raw')
    print("  [DIAG] R39_PRISTINE.flag set -> R39 ships PRISTINE (original quest data)")

# ===== STEP 7: Rebuild PACKDATA =====
print("\n=== Step 7: Rebuild PACKDATA.DIG ===")
rc = os.system('python build/rebuild_packdata.py')
if rc != 0:
    print('FATAL: Step 7 (rebuild_packdata.py) failed -- a truncated PACKDATA.DIG must never ship')
    sys.exit(1)

# ===== STEP 8: Build ISO =====
print("\n=== Step 8: Build ISO ===")
d = open('build/PACKDATA_v3.DIG', 'rb').read()
shutil.copy2('Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso', 'build/BUSIN0_EN_v9.iso')
with open('build/BUSIN0_EN_v9.iso', 'r+b') as iso:
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        if 'PACKDATA' in name:
            pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
            iso.seek(root_lba * SECTOR + pos + 10)
            iso.write(struct.pack('<I', len(d)))
            iso.write(struct.pack('>I', len(d)))
            iso.seek(pack_lba * SECTOR)
            iso.write(d)
            break
        pos += rec_len

# ===== STEP 8.2: Fix PACKDATA overflow into BSN2_0.DSI =====
# If our PACKDATA grew past the original end, shift all subsequent files
# forward to prevent overwriting BSN2_0.DSI (audio) and other files.
print("\n=== Step 8.2: Check PACKDATA overflow ===")
with open('build/BUSIN0_EN_v9.iso', 'r+b') as iso:
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    iso.seek(root_lba * SECTOR)
    root_dir = bytearray(iso.read(root_size))

    # Parse all directory entries
    dir_entries = []
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        dir_entries.append((pos, name, lba, size))
        pos += rec_len

    # Find PACKDATA end and first file after it
    pack_entry = [e for e in dir_entries if 'PACKDATA' in e[1]]
    if pack_entry:
        _, _, pack_lba, pack_size = pack_entry[0]
        pack_end_lba = pack_lba + math.ceil(pack_size / SECTOR)

        # Find all files after PACKDATA's START (they could be within the
        # overflow zone). Use pack_lba, not pack_end_lba, to catch files
        # that started right after the ORIGINAL (smaller) PACKDATA.
        after_pack = sorted(
            [e for e in dir_entries if e[2] > pack_lba and 'PACKDATA' not in e[1]],
            key=lambda e: e[2]
        )

        # ----- non-empty relocation list (anti-clobber tripwire) -----
        # The self-heal below ONLY runs inside `if after_pack:`. If the directory
        # parse ever returns an EMPTY list (parse bug / changed layout), the
        # entire shift is skipped silently while PACKDATA still overflows
        # BSN2_0.DSI -- a clobbered ISO ships with corrupt audio on real PS2.
        # There is ALWAYS at least BSN2_0.DSI after PACKDATA, so an empty list
        # here means the parse broke: fail the build loudly instead.
        assert after_pack, (
            "Step 8.2: no files found after PACKDATA.DIG -- the root-directory "
            "parse returned an empty relocation list; the overflow self-heal "
            "would silently no-op and ship a clobbered BSN2_0.DSI. Aborting."
        )

        if after_pack:
            first_after_lba = after_pack[0][2]
            shift_applied = 0  # set in BOTH branches; asserted after the if/else
            if pack_end_lba > first_after_lba:
                shift = pack_end_lba - first_after_lba
                shift_applied = shift
                print(f"  PACKDATA overflow: {shift} sectors into subsequent files")
                print(f"  Shifting {len(after_pack)} files forward by {shift} sectors...")

                # Read relocated files from the ORIGINAL ISO, not the working copy.
                # PACKDATA was written into the working ISO in Step 8, overwriting
                # the first N sectors of BSN2_0.DSI. Reading from the working ISO
                # would copy PACKDATA garbage into the relocated BSN2_0.DSI.
                orig_iso = open('Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso', 'rb')

                # Shift files in REVERSE order (last first) to avoid overwriting
                for dir_off, name, old_lba, fsize in reversed(after_pack):
                    new_lba = old_lba + shift
                    sec_count = math.ceil(fsize / SECTOR)
                    # Read file data from ORIGINAL ISO (not working copy)
                    orig_iso.seek(old_lba * SECTOR)
                    fdata = orig_iso.read(sec_count * SECTOR)
                    # Write to new position
                    iso.seek(new_lba * SECTOR)
                    iso.write(fdata)
                    # Update directory entry LBA (both LE and BE)
                    struct.pack_into('<I', root_dir, dir_off + 2, new_lba)
                    struct.pack_into('>I', root_dir, dir_off + 6, new_lba)

                orig_iso.close()

                # Write updated directory
                iso.seek(root_lba * SECTOR)
                iso.write(root_dir)

                # Extend ISO to accommodate shifted content
                iso.seek(0, 2)
                current_size = iso.tell()
                needed = (after_pack[-1][2] + shift + math.ceil(after_pack[-1][3] / SECTOR)) * SECTOR
                if needed > current_size:
                    iso.seek(needed - 1)
                    iso.write(b'\x00')

                # Also update PVD volume space size if needed
                new_vol_sectors = math.ceil(needed / SECTOR)
                iso.seek(16 * SECTOR + 80)
                iso.write(struct.pack('<I', new_vol_sectors))
                iso.write(struct.pack('>I', new_vol_sectors))

                print(f"  Done. ISO extended by {shift * SECTOR:,} bytes")
            else:
                print(f"  No overflow (PACKDATA ends at {pack_end_lba}, next file at {first_after_lba})")

            # ----- STEP 8.2 build-gate assert (real-PS2 audio safety) -----
            # The self-heal above is the ONLY thing standing between a broken
            # directory parse and silently corrupted BSN2_0.DSI audio. If the
            # parse ever breaks and Step 8.2 no-op's while PACKDATA actually
            # overflowed, we MUST fail the build rather than ship corrupt audio.
            # NEVER assert overflow==0 -- Step 8.2 self-heals, so that is normal.
            overflowed = pack_end_lba > first_after_lba
            assert (not overflowed) or shift_applied > 0, (
                "Step 8.2: PACKDATA overflowed (%d sectors) but no shift was "
                "applied -- self-heal silently no-op'd; BSN2_0.DSI audio would "
                "be corrupted on real PS2 hardware"
                % (pack_end_lba - first_after_lba)
            )
            if overflowed and shift_applied > 0:
                # Re-read the relocated first 'after PACKDATA' file (BSN2_0.DSI
                # in practice) at its NEW position and prove it is real file
                # content, not the PACKDATA bytes that Step 8 wrote over its
                # ORIGINAL sectors. The relocated first sector must differ from
                # PACKDATA's first sector (global `d`).
                _, _reloc_name, _reloc_old_lba, _ = after_pack[0]
                _reloc_new_lba = _reloc_old_lba + shift_applied
                iso.seek(_reloc_new_lba * SECTOR)
                _reloc_first = iso.read(SECTOR)
                assert _reloc_first != d[:SECTOR], (
                    "Step 8.2: relocated %s first sector at LBA %d == PACKDATA "
                    "first sector -- self-heal copied PACKDATA garbage instead "
                    "of original audio; real-PS2 audio would be corrupted"
                    % (_reloc_name, _reloc_new_lba)
                )
                print(f"  [gate] Step 8.2 verified: {_reloc_name} relocated to "
                      f"LBA {_reloc_new_lba}, first sector is original content")

# ===== STEP 8.4: Patch EXE =====
print("\n=== Step 8.4: Patch EXE ===")
rc = os.system('python build/patch_exe.py')
if rc != 0:
    print('FATAL: Step 8.4 (patch_exe.py) failed -- refusing to embed a stale/unpatched EXE')
    sys.exit(1)

# ===== STEP 8.5: Patch EXE into ISO =====
print("\n=== Step 8.5: Patch EXE ===")
exe_path = 'build/SLPM_653.78_patched'
if os.path.exists(exe_path):
    exe_data = open(exe_path, 'rb').read()
    with open('build/BUSIN0_EN_v9.iso', 'r+b') as iso:
        iso.seek(16 * SECTOR)
        pvd = iso.read(SECTOR)
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        iso.seek(root_lba * SECTOR)
        root_dir = iso.read(root_size)
        pos = 0
        while pos < len(root_dir):
            rec_len = root_dir[pos]
            if rec_len == 0:
                break
            name_len = root_dir[pos + 32]
            name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
            if 'SLPM' in name:
                exe_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
                iso.seek(root_lba * SECTOR + pos + 10)
                iso.write(struct.pack('<I', len(exe_data)))
                iso.write(struct.pack('>I', len(exe_data)))
                iso.seek(exe_lba * SECTOR)
                iso.write(exe_data)
                print(f"  EXE patched: {len(exe_data):,} bytes at LBA {exe_lba}")
                break
            pos += rec_len
else:
    print("  No patched EXE found, skipping")

print(f"\n{'=' * 60}")
print(f"  BUSIN0_EN_v9.iso built ({len(d):,} bytes)")
print(f"  Variable-size + Section 1 opcode patching + EXE")
print(f"{'=' * 60}")
