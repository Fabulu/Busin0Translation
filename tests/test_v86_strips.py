#!/usr/bin/env python3
"""
test_v86_strips.py -- v86 wave-2 regression suite.

Every resource the v86 patch wave re-renders text into (font-atlas "strips" of
PSMT4 glyph cells, plus the R34/R2654 MSG string tables) gets four guarantees:

  1. SIZE      -- the build output is the exact byte size of the pristine
                  extract (no truncation, no runaway growth).
  2. CONTAIN   -- every byte that differs from pristine lies inside a declared
                  writable window.  The integrity-critical prefixes/suffixes
                  (R2124 VIF/GIF display lists, R2147's EE-patched header) MUST
                  be byte-identical -- this is the v83 VIF-FIFO crash class.
  3. RENDERED  -- each patched window, deswizzled as PSMT4, has pixels that
                  actually DIFFER from pristine (English glyphs were drawn, the
                  patcher did not silently no-op).
  4. SHARED    -- resources that re-use a sibling's rendered strip
                  (R2155<-R2147, R2153<-R2150) match byte-for-byte.

Plus structural gates: R1188 must NOT be touched (v85 BUG-3), the chargen
resources must still ship patched, and R34/R2654 walk as valid MSG tables with
no leftover chargen-pollution glyph ids.

All paths absolute; SKIP when a build/ISO tier input is absent; FAIL only on a
real violation.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PackData,
    PACKDATA_RES_DIR,
    RAW_DIR,
    ROOT,
    SECTOR,
    Skip,
    default_iso_path,
)

# psmt4_deswizzle lives in tools/, already on sys.path via _helpers.
from psmt4_deswizzle import deswizzle_psmt4


# ===========================================================================
# MANIFEST -- one entry per v86-patched resource.
#
#   id        : PACKDATA resource index
#   fname     : exact <idddd>_type<NN>.raw filename in both pristine + build dirs
#   size      : exact pristine byte size (build output must match)
#   windows   : list of (start, end) byte ranges the patcher may write into.
#               Empty list => windows are DATA-DERIVED at test time (R2141/R2144),
#               see _derived_windows().
#   prefix_id : optional (start, end) that MUST stay byte-identical to pristine
#               (integrity region -- VIF/GIF/EE display list).
#   desw      : (tex_w, tex_h, bw, dbw) deswizzle params for a 0x8000-byte
#               (256x256) or 0x20000-byte (512x512) PSMT4 strip.
#
# NOTE on sizes that differ from the task brief:
#   * R1363 is 40960 (not 36864) on disc -- the actual pristine size is used.
#   * R34 ships at 58 sectors and R2654 at 110 sectors BY DESIGN; the sequential
#     TOC has no structural ceiling.  R34 is sanity-bounded at the injector's
#     80-sector runaway guard; R2654's size is only recorded.
# ===========================================================================

DESW_256 = (256, 256, 128, 128)      # 0x8000-byte PSMT4 strip
DESW_512 = (512, 512, 256, 256)      # 0x20000-byte PSMT4 strip (R2880)

# windows are full PSMT4 strips of 0x8000 bytes unless noted.
W = 0x8000

MANIFEST = [
    # id,   fname,               size,    windows,                              prefix_id,        desw
    dict(id=2124, fname="2124_type01.raw", size=34816,
         windows=[(0x2E0, 0x82E0)], prefix=(0, 0x2E0), suffix=(0x82E0, None),
         desw=DESW_256),
    dict(id=1365, fname="1365_type02.raw", size=38912,
         windows=[(1920, 34688)], desw=DESW_256),
    dict(id=1054, fname="1054_type02.raw", size=36864,
         windows=[(1312, 34080)], desw=DESW_256),
    dict(id=1360, fname="1360_type02.raw", size=36864,
         windows=[(1312, 34080)], desw=DESW_256),
    dict(id=1361, fname="1361_type02.raw", size=36864,
         windows=[(1312, 34080)], desw=DESW_256),
    dict(id=1362, fname="1362_type02.raw", size=36864,
         windows=[(1312, 34080)], desw=DESW_256),
    dict(id=1363, fname="1363_type02.raw", size=40960,
         windows=[(3808, 36576)], desw=DESW_256),
    dict(id=1364, fname="1364_type04.raw", size=71680,
         windows=[(1920, 34688)], desw=DESW_256),
    dict(id=1359, fname="1359_type02.raw", size=36864,
         windows=[(1312, 34080)], desw=DESW_256),
    dict(id=1367, fname="1367_type02.raw", size=36864,
         windows=[(1904, 34672)], desw=DESW_256),
    dict(id=1910, fname="1910_type02.raw", size=36864,
         windows=[(1840, 34608)], desw=DESW_256),
    # R2141/R2144: windows are derived from the patcher diff (see _derived_windows)
    dict(id=2141, fname="2141_type02.raw", size=69632, windows=[], desw=DESW_256),
    dict(id=2144, fname="2144_type02.raw", size=69632, windows=[], desw=DESW_256),
    dict(id=2150, fname="2150_type05.raw", size=147456,
         windows=[(1360, 34128), (36384, 69152), (71008, 103776), (105616, 138384)],
         desw=DESW_256),
    dict(id=2153, fname="2153_type05.raw", size=147456,
         windows=[(1360, 34128), (36384, 69152), (71008, 103776), (105616, 138384)],
         desw=DESW_256),
    # R2147: TWO distinct windows (0x12020 == 73760 is the SAME window, not three)
    dict(id=2147, fname="2147_type06.raw", size=382976,
         windows=[(0x560, 0x8560), (0x12020, 0x1A020)], prefix=(0, 0x560),
         desw=DESW_256),
    dict(id=2155, fname="2155_type10.raw", size=274432,
         windows=[(0x9920, 0x11920)], desw=DESW_256),
    dict(id=1370, fname="1370_type04.raw", size=81920,
         windows=[(3808, 36576)], desw=DESW_256),
    dict(id=2880, fname="2880_type11.raw", size=2113536,
         windows=[(1962944, 2094016)], desw=DESW_512),
    dict(id=2881, fname="2881_type15.raw", size=2316288,
         windows=[(1978608, 2109680), (2109744, 2240816)], desw=DESW_512),
]

# R2141/R2144 sub-resource windows (the patcher writes into FFFF-group glyph
# streams inside sub0 and a second sub).  The exact aux offset varies, so the
# test derives clusters from the diff and only asserts that the FIRST cluster
# lands in the sub0 window and the whole struct header (< 1312) is preserved.
SUB0_WINDOW = (1312, 34080)

# Chargen-pollution glyph ids that R34 must NOT contain after v86 (the kana/kanji
# block + the specific stat/keyboard ids eliminated in the v84/v85 work).
FORBIDDEN_GLYPHS = set(range(121, 147)) | {
    308, 320, 346, 354, 535, 582, 590, 672, 673, 696, 717, 718, 719, 720, 721
}

R34_SANITY_SECTORS = 80              # injector runaway-guard ceiling

_PACK = None


# ===========================================================================
# IO helpers
# ===========================================================================
def _pristine(fname):
    p = os.path.join(RAW_DIR, fname)
    if not os.path.isfile(p):
        raise Skip("pristine %s missing" % fname)
    return open(p, "rb").read()


def _build(fname):
    p = os.path.join(PACKDATA_RES_DIR, fname)
    if not os.path.isfile(p):
        raise Skip("build/packdata_resources/%s missing (run a build)" % fname)
    return open(p, "rb").read()


_ISO_PATH = None


def _iso_choice():
    global _ISO_PATH
    if _ISO_PATH is None:
        v86 = os.path.join(ROOT, "build", "BUSIN0_EN_v86.iso")
        v9 = os.path.join(ROOT, "build", "BUSIN0_EN_v9.iso")
        env = os.environ.get("BUSIN_ISO")
        if env and os.path.isfile(env):
            _ISO_PATH = env
        elif os.path.isfile(v86):
            _ISO_PATH = v86
        elif os.path.isfile(v9):
            _ISO_PATH = v9
        else:
            _ISO_PATH = ""
    return _ISO_PATH


def _pack():
    """ISO PackData reader; prefer v86, fall back to v9.  SKIP if neither."""
    global _PACK
    if _PACK is None:
        iso = _iso_choice()
        if not iso or not os.path.isfile(iso):
            raise Skip("no v86/v9 ISO present")
        _PACK = PackData(iso)
    return _PACK


def _require_fresh_iso(build_path):
    """SKIP the ISO comparison when the chosen ISO predates the build output --
    that means no post-v86 ISO has been built yet (the on-disc v9 is stale),
    NOT that the ISO is corrupt.  A freshly built v86 ISO will be newer and the
    comparison runs for real."""
    iso = _iso_choice()
    if not iso or not os.path.isfile(iso):
        raise Skip("no v86/v9 ISO present")
    if os.path.getmtime(iso) < os.path.getmtime(build_path):
        raise Skip(
            "ISO %s predates build output -- no fresh v86 ISO built yet"
            % os.path.basename(iso)
        )


def _diff_offsets(a, b):
    n = min(len(a), len(b))
    return [i for i in range(n) if a[i] != b[i]]


def _clusters(offsets, gap=1024):
    if not offsets:
        return []
    cl = []
    s = prev = offsets[0]
    for i in offsets[1:]:
        if i - prev > gap:
            cl.append((s, prev + 1))
            s = i
        prev = i
    cl.append((s, prev + 1))
    return cl


def _strip(data, win, desw):
    """Deswizzle the PSMT4 strip at win=(start,end) using desw params."""
    tw, th, bw, dbw = desw
    pix_bytes = tw * th // 2
    chunk = data[win[0]:win[0] + pix_bytes]
    return deswizzle_psmt4(chunk, tw, th, bw_psmt4=bw, dbw_ct32=dbw)


# ===========================================================================
# R34 / R2654 MSG structural walk
# ===========================================================================
def _seq_table(d):
    """Walk the 16-byte sequential sub-resource table at offset 16.

    Each entry: (id u32, size u32, offset u32, 0).  ids run 1,2,3,...; the walk
    stops at the first non-sequential id.  Returns [(id, size, offset)].
    """
    seq = []
    e = 0
    while True:
        base = 16 + e * 16
        if base + 16 > len(d):
            break
        vid, sz, off, _z = struct.unpack_from("<IIII", d, base)
        if vid != e + 1:
            break
        seq.append((vid, sz, off))
        e += 1
    return seq


def _parse_ot(sub):
    """Format-A offset table at the head of a sub: (count u16, 0), entries
    (offset u16, flags u16) with flags==0xFFFF on the last.  Returns
    (count, table_byte_size) or None when the sub is not Format-A text."""
    if len(sub) < 4:
        return None
    cnt = struct.unpack_from(">H", sub, 0)[0]
    f0 = struct.unpack_from(">H", sub, 2)[0]
    if f0 != 0 or cnt < 1 or cnt > 2000:
        return None
    i = 4
    for _e in range(cnt):
        if i + 4 > len(sub):
            return None
        fl = struct.unpack_from(">H", sub, i + 2)[0]
        i += 4
        if fl == 0xFFFF:
            return cnt, i
    return cnt, i


def _walk_msg(d, name):
    """Structural walk of an R34/R2654-style type20/type44 resource.

    Returns (seq, issues).  issues == [] means the structure is consistent:
      * >= 1 sequential sub, ids contiguous from 1,
      * sub offsets strictly ascending, every sub fully inside the file,
      * each Format-A sub: offset table ends on a 0xFFFF sentinel, and its
        string payload ends FFFE FFFF.
    """
    issues = []
    seq = _seq_table(d)
    if not seq:
        issues.append("%s: no sequential sub-resource table" % name)
        return seq, issues
    prev = -1
    for vid, sz, off in seq:
        if off <= prev:
            issues.append("%s: sub %d offset %d not ascending" % (name, vid, off))
        prev = off
        if off + sz > len(d):
            issues.append(
                "%s: sub %d [%d:%d] exceeds file (%d)"
                % (name, vid, off, off + sz, len(d))
            )
            continue
        sub = d[off:off + sz]
        ot = _parse_ot(sub)
        if ot is None:
            continue  # binary / non-text sub -- structural walk skips it
        _cnt, tsize = ot
        payload = sub[tsize:]
        if len(payload) >= 4 and payload[-4:] != b"\xff\xfe\xff\xff":
            issues.append(
                "%s: sub %d string payload does not end FFFE FFFF (ends %s)"
                % (name, vid, payload[-4:].hex())
            )
    return seq, issues


def _glyph_stream_ids(d):
    """Decoded glyph ids from every Format-A sub's string stream (FFFF/FFFE
    delimiters excluded).  Used for the forbidden-glyph gate."""
    ids = []
    for _vid, sz, off in _seq_table(d):
        if off + sz > len(d):
            continue
        sub = d[off:off + sz]
        ot = _parse_ot(sub)
        if ot is None:
            continue
        _cnt, tsize = ot
        stream = sub[tsize:]
        for i in range(0, len(stream) - 1, 2):
            w = struct.unpack_from(">H", stream, i)[0]
            if w in (0xFFFF, 0xFFFE):
                continue
            ids.append(w)
    return ids


# ===========================================================================
# Per-resource checks driven by MANIFEST
# ===========================================================================
def _check_size(entry):
    fname = entry["fname"]
    bd = _build(fname)
    pr = _pristine(fname)
    assert len(bd) == entry["size"], (
        "R%d %s: build size %d != expected %d"
        % (entry["id"], fname, len(bd), entry["size"])
    )
    assert len(bd) == len(pr), (
        "R%d %s: build size %d != pristine %d"
        % (entry["id"], fname, len(bd), len(pr))
    )


def _windows_for(entry, pr, bd):
    """Resolve declared or data-derived writable windows."""
    if entry["windows"]:
        return entry["windows"]
    # Derived (R2141/R2144): clusters from the diff; header (< sub0 start) must
    # be preserved and the first cluster must land inside the sub0 window.
    offs = _diff_offsets(pr, bd)
    cl = _clusters(offs)
    assert cl, "R%d: no diff at all -- patcher never ran" % entry["id"]
    first = cl[0]
    assert first[0] >= SUB0_WINDOW[0], (
        "R%d: diff starts at 0x%x, inside the preserved struct header (< 0x%x)"
        % (entry["id"], first[0], SUB0_WINDOW[0])
    )
    assert first[1] <= SUB0_WINDOW[1], (
        "R%d: first diff cluster 0x%x..0x%x overruns the sub0 window (1312,34080)"
        % (entry["id"], first[0], first[1])
    )
    return cl


def _check_containment(entry):
    fname = entry["fname"]
    pr, bd = _pristine(fname), _build(fname)
    end = len(bd)
    # integrity prefix / suffix must be byte-identical.
    if "prefix" in entry:
        a, b = entry["prefix"]
        assert pr[a:b] == bd[a:b], (
            "R%d: integrity prefix [0x%x:0x%x] differs -- v83 VIF/GIF crash class"
            % (entry["id"], a, b)
        )
    if entry.get("suffix"):
        a, b = entry["suffix"]
        b = end if b is None else b
        assert pr[a:b] == bd[a:b], (
            "R%d: integrity suffix [0x%x:0x%x] differs -- v83 VIF/GIF crash class"
            % (entry["id"], a, b)
        )
    wins = _windows_for(entry, pr, bd)
    offs = _diff_offsets(pr, bd)
    stray = [i for i in offs if not any(s <= i < e for (s, e) in wins)]
    assert not stray, (
        "R%d: %d byte diff(s) OUTSIDE declared windows %s (first at 0x%x)"
        % (entry["id"], len(stray), wins, stray[0])
    )


def _check_rendered(entry):
    fname = entry["fname"]
    pr, bd = _pristine(fname), _build(fname)
    wins = _windows_for(entry, pr, bd)
    # For derived windows the clusters are not full strips; fall back to a raw
    # byte-diff non-emptiness check.  For declared full-strip windows, deswizzle
    # and require the rendered pixels to differ.
    rendered = False
    for win in wins:
        tw, th, _bw, _dbw = entry["desw"]
        need = tw * th // 2
        if win[1] - win[0] >= need:
            pp = _strip(pr, win, entry["desw"])
            bb = _strip(bd, win, entry["desw"])
            if pp != bb:
                rendered = True
                break
        else:
            if pr[win[0]:win[1]] != bd[win[0]:win[1]]:
                rendered = True
                break
    assert rendered, (
        "R%d: no patched window's pixels differ from pristine -- English text "
        "was not rendered into the atlas" % entry["id"]
    )


# Build the per-entry test functions dynamically so each resource reports its
# own PASS/FAIL/SKIP line (matching the conventions of the existing suite).
def _make(entry, kind):
    fns = {
        "size": _check_size,
        "contain": _check_containment,
        "render": _check_rendered,
    }
    check = fns[kind]

    def fn():
        check(entry)

    fn.__name__ = "test_R%d_%s" % (entry["id"], kind)
    fn.__doc__ = "R%d (%s): %s" % (entry["id"], entry["fname"], kind)
    return fn


# ===========================================================================
# Shared-strip cross-resource checks
# ===========================================================================
def test_R2155_hint_equals_R2147_window():
    a = _build("2147_type06.raw")[0x12020:0x1A020]
    b = _build("2155_type10.raw")[0x9920:0x11920]
    assert len(a) == len(b) == 0x8000, "strip lengths %d/%d" % (len(a), len(b))
    assert a == b, (
        "R2155 hint strip is NOT byte-identical to R2147[0x12020:0x1A020] -- "
        "the shared rendered strip diverged"
    )


def test_R2153_strips_equal_R2150():
    g2150 = _build("2150_type05.raw")
    g2153 = _build("2153_type05.raw")
    for off in (36384, 71008, 105616):
        a = g2150[off:off + W]
        b = g2153[off:off + W]
        assert a == b, (
            "R2153 strip @%d is NOT byte-identical to R2150 -- shared rendered "
            "strip diverged" % off
        )


# ===========================================================================
# Gate checks: R1188, chargen, R34/R2654
# ===========================================================================
def test_R1188_not_repatched():
    """v85 BUG-3: the live dialogue font must NOT be written into."""
    p = os.path.join(PACKDATA_RES_DIR, "1188_type01.raw")
    if not os.path.isfile(p):
        return  # absent == not patched == correct
    bd = open(p, "rb").read()
    pr = _pristine("1188_type01.raw")
    assert bd == pr, (
        "build/packdata_resources/1188_type01.raw exists and DIFFERS from "
        "pristine -- a patcher is writing into the dialogue font again (BUG-3)"
    )


def test_chargen_resources_shipped_patched():
    """R2100 + R2138 must still differ from pristine (chargen English shipping).
    SKIP if absent -- they are produced by earlier build steps that may not have
    run in a partial wave-2 state."""
    for fname in ("2100_type04.raw", "2138_type29.raw"):
        bp = os.path.join(PACKDATA_RES_DIR, fname)
        if not os.path.isfile(bp):
            raise Skip("%s absent (earlier build step not run)" % fname)
        bd = open(bp, "rb").read()
        pr = _pristine(fname)
        assert bd != pr, (
            "%s is byte-identical to pristine -- chargen English patch no longer "
            "shipping" % fname
        )


def test_R34_structural_and_glyphs():
    bd = _build("0034_type20.raw")
    _seq, issues = _walk_msg(bd, "R34")
    assert not issues, "R34 structure: %s" % "; ".join(issues[:5])
    # size sanity (injector runaway guard), NOT the discarded 40-sector estimate
    assert len(bd) <= R34_SANITY_SECTORS * SECTOR, (
        "R34 is %d bytes (> %d-sector runaway guard) -- injector overran"
        % (len(bd), R34_SANITY_SECTORS)
    )
    bad = sorted(set(g for g in _glyph_stream_ids(bd) if g in FORBIDDEN_GLYPHS))
    assert not bad, (
        "R34 string streams still contain chargen-pollution glyph ids %s"
        % bad[:20]
    )


def test_R2654_structural_and_translations():
    bd = _build("2654_type44.raw")
    _seq, issues = _walk_msg(bd, "R2654")
    assert not issues, "R2654 structure: %s" % "; ".join(issues[:5])
    # No upper-bound failure on size -- just record it.
    sectors = (len(bd) + SECTOR - 1) // SECTOR
    print("    (R2654 ships at %d bytes / %d sectors)" % (len(bd), sectors))
    # Step-2 co-op translations preserved: at least one sub must differ from
    # pristine.  (The co-op strings live in sub id 11, not sub0, so the gate is
    # "a sub changed", which proves the injection applied.)
    pr = _pristine("2654_type44.raw")
    pseq = _seq_table(pr)
    bseq = _seq_table(bd)
    changed = []
    for i in range(min(len(pseq), len(bseq))):
        _pv, psz, poff = pseq[i]
        _bv, bsz, boff = bseq[i]
        if pr[poff:poff + psz] != bd[boff:boff + bsz]:
            changed.append(i)
    assert changed, (
        "R2654: every sub-resource is byte-identical to pristine -- the Step-2 "
        "co-op translations were not injected"
    )


# ===========================================================================
# ISO tier: round-trip a few resources straight out of the ISO and compare to
# the build/packdata_resources copies.
# ===========================================================================
def _iso_compare(idx, fname, header_region=None):
    bp = os.path.join(PACKDATA_RES_DIR, fname)
    if not os.path.isfile(bp):
        raise Skip("build/packdata_resources/%s absent for ISO compare" % fname)
    _require_fresh_iso(bp)
    pk = _pack()
    build_bytes = open(bp, "rb").read()
    if header_region is not None:
        # R1370 lives in the PACKDATA header gap (sectors 85-124), not the TOC.
        lo, hi = header_region
        pk.fh.seek((pk.pack_lba + lo) * SECTOR)
        region = pk.fh.read((hi - lo + 1) * SECTOR)
        iso_bytes = region[: len(build_bytes)]
    else:
        data, _tc = pk.extract(idx)
        iso_bytes = data[: len(build_bytes)]
    assert iso_bytes == build_bytes, (
        "R%d in the ISO does not match build/packdata_resources/%s "
        "(first %d bytes compared)" % (idx, fname, len(build_bytes))
    )


def test_iso_R2124_matches_build():
    _iso_compare(2124, "2124_type01.raw")


def test_iso_R1365_matches_build():
    _iso_compare(1365, "1365_type02.raw")


def test_iso_R2147_matches_build():
    _iso_compare(2147, "2147_type06.raw")


def test_iso_R34_matches_build():
    _iso_compare(34, "0034_type20.raw")


def test_iso_R1370_matches_build():
    # R1370 is patched into the PACKDATA header region (sectors 85-124).
    _iso_compare(1370, "1370_type04.raw", header_region=(85, 124))


# ===========================================================================
# Assemble TESTS
# ===========================================================================
TESTS = []
for _e in MANIFEST:
    TESTS.append(_make(_e, "size"))
    TESTS.append(_make(_e, "contain"))
    TESTS.append(_make(_e, "render"))

TESTS += [
    test_R2155_hint_equals_R2147_window,
    test_R2153_strips_equal_R2150,
    test_R1188_not_repatched,
    test_chargen_resources_shipped_patched,
    test_R34_structural_and_glyphs,
    test_R2654_structural_and_translations,
    test_iso_R2124_matches_build,
    test_iso_R1365_matches_build,
    test_iso_R2147_matches_build,
    test_iso_R34_matches_build,
    test_iso_R1370_matches_build,
]


if __name__ == "__main__":
    from _helpers import main_exit

    main_exit(TESTS, "test_v86_strips")
