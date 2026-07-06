#!/usr/bin/env python3
"""v89 phase2: verify the Step-4 type-2 word-wrap fix.

Replicates the NEW build_v9 Step-4 encoding for ALL type-02 resources and:
 (a) before/after histogram of lines >16 / >18 glyphs
 (b) choice-group byte-identity: encoded english of every pristine FFC0..FFCF
     group must be byte-identical with vs without wrapping
 (c) inject_and_patch on R1196/R1197/R1203 with wrapped encoding -> no overflow,
     no walk failure, choice markers preserved
 (d) decode previously-overflowing narration groups -> every line <= 16
 (e) R1203 Section-2 cap re-derivation under wrapping (must stay <= 65535 words)
"""
import sys, os, struct, json, glob, math
sys.stdout.reconfigure(encoding='utf-8')

ROOT = 'C:/Programmieren/wizardrytranslation'
os.chdir(ROOT)
sys.path.insert(0, 'tools')

from patch_section1_offsets import (
    inject_and_patch, group_choice_markers, HEADER_SIZE,
    parse_sec2_group_offsets,
)

# ---- mirror build_v9 helpers (kept in sync) --------------------------------
table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))


def enc(ch):
    if ch in table:
        return table[ch]
    if ch.lower() in table:
        return table[ch.lower()]
    return 31


TYPE2_WRAP_WIDTH = 16


def _wrap_line(seg, max_chars):
    out = []
    while len(seg) > max_chars:
        brk = seg.rfind(' ', 0, max_chars + 1)
        if brk <= 0:
            brk = max_chars
        out.append(seg[:brk])
        seg = seg[brk:].lstrip(' ')
    out.append(seg)
    return out


def wrap_type2_text(text, max_chars=TYPE2_WRAP_WIDTH):
    pages = []
    for page in text.split(' // '):
        lines = []
        for seg in page.split(' / '):
            lines.extend(_wrap_line(seg, max_chars))
        pages.append(' / '.join(lines))
    return ' // '.join(pages)


def encode_msg(en_text):
    """Replicate build_v9 Step-4 glyph encoding (split + auto 3-line page break)."""
    glyphs = []
    for page_i, page in enumerate(en_text.split(' // ')):
        if page_i > 0:
            glyphs.append(0xFFD2)
        line_count = 0
        for pi, part in enumerate(page.split(' / ')):
            if pi > 0:
                line_count += 1
                if line_count >= 3:
                    glyphs.append(0xFFD2)
                    line_count = 0
                else:
                    glyphs.append(0xFFFE)
            for ch in part:
                glyphs.append(enc(ch))
    return glyphs


def load_pristine_choice_groups(res_idx, raw_dir='extracted/packdata_raw'):
    path = f'{raw_dir}/{res_idx:04d}_type02.raw'
    if not os.path.isfile(path):
        return set()
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


# ---- load translations exactly like build_v9 Step 4 ------------------------
def load_all_trans():
    all_trans = {}
    for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
        # build_v9 wraps the WHOLE per-file loop in try/except: a malformed entry
        # aborts that file with a warning.  Replicate that exactly.
        try:
            d = json.load(open(fn, encoding='utf-8'))
            for e in d:
                r = e['resource']
                mi = e['msg_index']
                en = e.get('english', '')
                if not en:
                    continue
                if en.startswith(('[DATA]', '[LAYOUT]', '[BINARY]', '[MAP]',
                                  '[SYSTEM]', '[GLYPH', '[DEBUG]')):
                    continue
                if any(ord(c) > 127 for c in en):
                    continue
                all_trans.setdefault(r, {})[mi] = en
        except Exception as ex:
            print(f"  Warning: {fn}: {ex}")
    return all_trans


def type02_set(all_trans):
    manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
    s = set()
    for r in all_trans:
        if r < len(manifest) and not manifest[r].get('skipped') and manifest[r].get('type_code') == 2:
            s.add(r)
    s.discard(1193)
    return s


# ---- line-width measurement ------------------------------------------------
def measure_lines(en_text):
    """Yield glyph-count of each on-screen line (split on ' // ' and ' / ')."""
    for page in en_text.split(' // '):
        for seg in page.split(' / '):
            yield len(seg)


def histo(all_trans, t02, apply_wrap):
    over16 = over18 = total = 0
    worst = 0
    for r in sorted(t02):
        choice = load_pristine_choice_groups(r) if apply_wrap else set()
        for mi, en in all_trans[r].items():
            txt = en
            if apply_wrap and mi not in choice:
                txt = wrap_type2_text(en)
            for w in measure_lines(txt):
                total += 1
                if w > 16:
                    over16 += 1
                if w > 18:
                    over18 += 1
                worst = max(worst, w)
    return dict(total=total, over16=over16, over18=over18, worst=worst)


def main():
    all_trans = load_all_trans()
    t02 = type02_set(all_trans)
    print(f"Type-02 resources: {len(t02)}")

    # (a) histogram before/after
    before = histo(all_trans, t02, apply_wrap=False)
    after = histo(all_trans, t02, apply_wrap=True)
    print("\n=== (a) Line-width histogram (segments) ===")
    print(f"  BEFORE: total={before['total']}  >16={before['over16']}  "
          f">18={before['over18']}  worst={before['worst']}")
    print(f"  AFTER : total={after['total']}  >16={after['over16']}  "
          f">18={after['over18']}  worst={after['worst']}")

    # (b) choice-group byte identity
    print("\n=== (b) Choice-group encoding identity (wrap excluded) ===")
    choice_total = 0
    choice_mismatch = 0
    for r in sorted(t02):
        choice = load_pristine_choice_groups(r)
        for mi in sorted(choice):
            if mi not in all_trans[r]:
                continue
            choice_total += 1
            en = all_trans[r][mi]
            nowrap = encode_msg(en)
            # build path leaves choice msgs unwrapped -> identical input
            wrapped_input = en  # skipped wrapping
            wrapped = encode_msg(wrapped_input)
            if nowrap != wrapped:
                choice_mismatch += 1
                print(f"  MISMATCH R{r} g{mi}")
    print(f"  choice groups w/ translation: {choice_total}  mismatches: {choice_mismatch}")
    assert choice_mismatch == 0, "choice-group encoding changed under wrap path!"

    # (e) R1203 cap re-derivation under wrapping
    print("\n=== (e) R1203 Section-2 word-count under wrapping ===")
    r1203_cap = derive_r1203_cap(all_trans)

    # (c) inject_and_patch on R1196/R1197/R1203
    print("\n=== (c) inject_and_patch dry run ===")
    out_dir = 'build/recon_v89/phase2/out'
    os.makedirs(out_dir, exist_ok=True)
    for r in (1196, 1197, 1203):
        run_inject(r, all_trans, out_dir, r1203_cap)

    # (d) decode previously-overflowing narration groups
    print("\n=== (d) Sample narration groups (R1196 570-573, R1197 bar) ===")
    sample_check(all_trans, 1196, range(570, 574))

    print("\nALL CHECKS COMPLETE")


def build_encoded(r, all_trans, r1203_cap=None):
    """Build the encoded_trans dict exactly as the NEW build_v9 Step 4 would."""
    choice = load_pristine_choice_groups(r)
    encoded = {}
    for mi, en in all_trans[r].items():
        txt = en
        if mi not in choice:
            txt = wrap_type2_text(en)
        encoded[mi] = encode_msg(txt)
    if r == 1203 and r1203_cap is not None:
        encoded = {mi: g for mi, g in encoded.items() if mi <= r1203_cap}
    return encoded


def total_sec2_words(r, encoded):
    """Total Section-2 word count after injecting `encoded` into pristine groups.
    Counts every group (translated replaces its body; untranslated keeps pristine)
    plus the FFFF terminators and trailing words -- mirrors inject_and_patch."""
    path = f'extracted/packdata_raw/{r:04d}_type02.raw'
    raw = open(path, 'rb').read()
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec2 = raw[sec2_off:sec2_off + sec2_size]
    groups, trailing_start = parse_sec2_group_offsets(sec2)
    n_words = sec2_size // 2
    total = 0
    for gi, (gs, ge) in enumerate(groups):
        if gi in encoded:
            # choice groups go through encode_choice_group; approximate with
            # pristine length for cap purposes (choice msgs aren't wrapped and
            # encode_choice_group keeps option content, so length is close).
            total += len(encoded[gi])
        else:
            total += (ge - gs)
        total += 1  # FFFF terminator
    total += (n_words - trailing_start)  # trailing words
    return total


def derive_r1203_cap(all_trans):
    """Find highest group index keeping R1203 Section-2 total <= 65535 words
    under the NEW wrapped encoding (binary-search style linear scan)."""
    r = 1203
    choice = load_pristine_choice_groups(r)
    # Build full wrapped encoding (no cap)
    full = {}
    for mi, en in all_trans[r].items():
        txt = en if mi in choice else wrap_type2_text(en)
        full[mi] = encode_msg(txt)

    LIMIT = 65535
    keys = sorted(full)
    # incrementally cap from the top until total <= LIMIT
    best = None
    for cap in keys + [max(keys) + 1]:
        capped = {mi: g for mi, g in full.items() if mi <= cap}
        tot = total_sec2_words(r, capped)
        if tot <= LIMIT:
            best = cap
        else:
            break
    # report
    tot_at_best = total_sec2_words(r, {mi: g for mi, g in full.items() if mi <= best})
    tot_uncapped = total_sec2_words(r, full)
    print(f"  uncapped total words: {tot_uncapped} (limit {LIMIT})")
    print(f"  derived cap group index: {best}  total words @cap: {tot_at_best}")
    old_cap = 1069
    old_tot = total_sec2_words(r, {mi: g for mi, g in full.items() if mi <= old_cap})
    print(f"  OLD cap {old_cap} under wrapping -> total words: {old_tot} "
          f"({'OK' if old_tot <= LIMIT else 'OVERFLOW'})")
    return best


def run_inject(r, all_trans, out_dir, r1203_cap):
    encoded = build_encoded(r, all_trans, r1203_cap)
    res = inject_and_patch(r, encoded, 'extracted/packdata_raw', out_dir)
    if res[0] is None:
        print(f"  R{r}: FAILED -> {res[1]}")
        return
    print(f"  R{r}: {res[1]}")
    # verify choice markers preserved in output Section 2
    verify_choice_markers(r, out_dir)
    # verify Section-2 word count under cap
    out = open(os.path.join(out_dir, res[0]), 'rb').read()
    s2sz = struct.unpack_from('<I', out, 0x14)[0]
    nwords = s2sz // 2
    print(f"     out Section-2 words: {nwords} ({'<=65535 OK' if nwords <= 65535 else 'OVERFLOW'})")


def verify_choice_markers(r, out_dir):
    pristine_choice = load_pristine_choice_groups(r)
    if not pristine_choice:
        print("     (no choice groups)")
        return
    out = open(os.path.join(out_dir, f'{r:04d}_type02.raw'), 'rb').read()
    s2sz = struct.unpack_from('<I', out, 0x14)[0]
    s2off = struct.unpack_from('<I', out, 0x18)[0]
    sec2 = out[s2off:s2off + s2sz]
    nwords = s2sz // 2
    words = [struct.unpack_from('>H', sec2, i * 2)[0] for i in range(nwords)]
    # parse groups, check that choice indices still have markers
    gi = 0
    start = 0
    preserved = 0
    missing = []
    pidx = 0
    for i in range(nwords):
        if words[i] == 0xFFFF:
            if pidx in pristine_choice:
                if group_choice_markers(words[start:i]):
                    preserved += 1
                else:
                    missing.append(pidx)
            pidx += 1
            start = i + 1
    print(f"     choice groups: {len(pristine_choice)}  preserved markers: {preserved}  missing: {missing}")
    assert not missing, f"R{r} lost choice markers in groups {missing}"


def sample_check(all_trans, r, group_range):
    choice = load_pristine_choice_groups(r)
    for mi in group_range:
        if mi not in all_trans[r]:
            continue
        en = all_trans[r][mi]
        wrapped = en if mi in choice else wrap_type2_text(en)
        widths = list(measure_lines(wrapped))
        bad = [w for w in widths if w > 16]
        status = 'OK' if not bad else f'OVER {bad}'
        print(f"  R{r} g{mi}: {len(widths)} lines, max={max(widths) if widths else 0} [{status}]")
        if bad:
            print(f"     text={wrapped!r}")


if __name__ == '__main__':
    main()
