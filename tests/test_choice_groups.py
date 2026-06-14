#!/usr/bin/env python3
"""
test_choice_groups.py -- structural integrity gate for CHOICE groups.

A "choice group" is a Section-2 FFFF group that the game treats as a branching
question + selectable options.  Each option is introduced by a marker word in
0xFFC0..0xFFCF (FFC0 = option 0, FFC1 = option 1, ...).  The choice->branch
linkage in Section 1 keys off these markers, so the marker SET (values, order
and count) of a group is load-bearing: dropping, adding, reordering or emptying
an option silently desyncs the menu from the branch table.

The Section-1 offset patcher re-flows the English text inside each group and
rewrites the DISPLAY_TEXT spans.  These tests pin down that the re-flow NEVER
disturbs the choice marker structure of any real choice group, end to end:

  TEST 1 (HARD)  every choice group's ordered FFC0..FFCF marker list survives
                 the build byte-for-byte; group count per resource is preserved;
                 the group still ends on its FFFF terminator.
  TEST 2 (HARD)  every INJECTED (text-changed) choice group has >=1 content word
                 after each marker -- no empty option.
  TEST 3 (HARD)  Section-1 integrity (sec1_regression_check) on every patched
                 choice resource -- protects the choice->branch linkage.
  TEST 4 (HARD)  global marker-count tripwire: total markers across CHOICE_SET
                 is identical pristine vs patched (no net loss/gain).
  TEST 5 (WARN)  semantic spot-check on a curated sample -- decodes question +
                 options, asserts question non-empty and decoded option count
                 matches marker count.  WARN-only (prints), never fails.
  TEST 6 (Tier3) re-runs TEST 1 + TEST 4 against the resources as they live in
                 the built PACKDATA (the real-PS2 path).  Skips with no ISO.

CHOICE_SET is built by build_choice_set(), which enumerates ONLY real choice
groups -- batch-translated entries (after build_v9's filters) whose PRISTINE
group carries >=1 FFC0..FFCF marker.  This deliberately excludes the ~8300
binary false-positive groups (no batch translation) and the binary resources.
"""

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    DATA_DIR,
    PATCHED_TYPE2_DIR,
    PackData,
    RAW_DIR,
    ROOT,
    Skip,
    decode_glyphs,
    default_iso_path,
    group_offsets,
    main_exit,
    parse_type02,
    require_dir,
    sec1_regression_check,
)

CHOICE_LO = 0xFFC0
CHOICE_HI = 0xFFCF
TYPE2_TRANS_DIR = os.path.join(DATA_DIR, "type2_translated")

# Curated injected choice groups for the TEST 5 semantic spot-check.
SEMANTIC_SAMPLE = [
    (1196, 330),
    (1197, 63),
    (1203, 452),
    (1199, 149),
    (1354, 122),
]


# ===========================================================================
# build_v9 translation filter (mirrors build/build_v9.py Step 4 exactly)
# ===========================================================================
_DROP_PREFIXES = ("[DATA]", "[LAYOUT]", "[BINARY]", "[MAP]", "[SYSTEM]", "[GLYPH", "[DEBUG]")


def _build_v9_keeps(en):
    """True iff build_v9 would inject this english string (same filter order)."""
    if not en:
        return False
    if en.startswith(_DROP_PREFIXES):
        return False
    if any(ord(c) > 127 for c in en):
        return False
    return True


# ===========================================================================
# Pristine type-02 cache + marker extraction
# ===========================================================================
def _pristine_raw_path(res):
    return os.path.join(RAW_DIR, "%04d_type02.raw" % res)


_PRISTINE_CACHE = {}


def _pristine_groups(res):
    """
    Return (words, groups) for the pristine type-02 extract of `res`, or None
    when the file is absent / does not parse as type-02.  Cached.
    """
    if res in _PRISTINE_CACHE:
        return _PRISTINE_CACHE[res]
    path = _pristine_raw_path(res)
    result = None
    if os.path.isfile(path):
        try:
            data = open(path, "rb").read()
            p = parse_type02(data)
            groups, _trailing = group_offsets(p["words"])
            result = (p["words"], groups)
        except Exception:
            result = None
    _PRISTINE_CACHE[res] = result
    return result


def _markers(words, group_span):
    """Ordered FFC0..FFCF marker list inside a (start, ffff_index) group span."""
    gs, ge = group_span
    return [w for w in words[gs:ge] if CHOICE_LO <= w <= CHOICE_HI]


# ===========================================================================
# SHARED ENUMERATION: the real choice groups
# ===========================================================================
_CHOICE_SET = None


def build_choice_set():
    """
    Enumerate every REAL choice group as (res, msg_index, pristine_markers).

    A group qualifies iff:
      * some batch_*.json entry (resource, msg_index, english) survives
        build_v9's injection filter (_build_v9_keeps), AND
      * the PRISTINE group at that msg_index carries >=1 FFC0..FFCF marker.

    Each batch file is processed inside its own try/except so a malformed file
    aborts at the same point build_v9 does (build_v9 wraps the per-file loop in
    `try/except Exception` and accesses e['msg_index'] directly -- e.g.
    batch_md_import.json has no msg_index key and is dropped whole).  Entries
    added before such an abort are kept, exactly like build_v9.

    The result is de-duplicated on (res, msg_index) (multiple batch files /
    duplicate entries collapse to one) and sorted.  Cached.
    """
    global _CHOICE_SET
    if _CHOICE_SET is not None:
        return _CHOICE_SET

    seen = {}  # (res, mi) -> pristine_markers
    for fn in sorted(glob.glob(os.path.join(TYPE2_TRANS_DIR, "batch_*.json"))):
        try:
            import json

            entries = json.load(open(fn, encoding="utf-8"))
            for e in entries:
                en = e.get("english", "")
                if not _build_v9_keeps(en):
                    continue
                res = e["resource"]
                mi = e["msg_index"]  # KeyError aborts this file, like build_v9
                if (res, mi) in seen:
                    continue
                pg = _pristine_groups(res)
                if pg is None:
                    continue
                words, groups = pg
                if mi < 0 or mi >= len(groups):
                    continue
                markers = _markers(words, groups[mi])
                if markers:
                    seen[(res, mi)] = markers
        except Exception:
            # Same fate as build_v9: a malformed file is dropped whole, keeping
            # whatever entries were already accepted from it.
            continue

    _CHOICE_SET = sorted(
        (res, mi, markers) for (res, mi), markers in seen.items()
    )
    return _CHOICE_SET


# ===========================================================================
# Patched-file helpers
# ===========================================================================
def _patched_raw_path(res):
    return os.path.join(PATCHED_TYPE2_DIR, "%04d_type02.raw" % res)


_PATCHED_CACHE = {}


def _patched_groups(res):
    """(words, groups) for the patched type-02 file of `res`, or None when the
    file is absent / unparsable.  Cached."""
    if res in _PATCHED_CACHE:
        return _PATCHED_CACHE[res]
    path = _patched_raw_path(res)
    result = None
    if os.path.isfile(path):
        try:
            data = open(path, "rb").read()
            p = parse_type02(data)
            groups, _trailing = group_offsets(p["words"])
            result = (p["words"], groups)
        except Exception:
            result = None
    _PATCHED_CACHE[res] = result
    return result


# ===========================================================================
# TEST 1 (HARD FAIL): marker-set preserved per choice group
# ===========================================================================
def test_marker_set_preserved():
    """Every patched choice group keeps its pristine FFC0..FFCF marker list
    EXACTLY (values + order + length), the resource keeps its group count, and
    the group still ends on a 0xFFFF terminator."""
    require_dir(PATCHED_TYPE2_DIR, "run a build first (Step 4 type-02 injection)")
    choice_set = build_choice_set()
    if not choice_set:
        raise Skip("CHOICE_SET empty (no batch translations / pristine extracts)")

    issues = []
    checked = 0
    for res, gi, pristine_markers in choice_set:
        pg = _patched_groups(res)
        if pg is None:
            continue  # this resource was not (re)built this run -- exempt
        pris = _pristine_groups(res)
        if pris is None:
            issues.append("R%d g%d: patched present but pristine missing" % (res, gi))
            continue
        p_words, p_groups = pg
        _o_words, o_groups = pris

        if len(p_groups) != len(o_groups):
            issues.append(
                "R%d: patched group_count %d != pristine %d"
                % (res, len(p_groups), len(o_groups))
            )
            continue
        if gi >= len(p_groups):
            issues.append("R%d g%d: group index out of range in patched" % (res, gi))
            continue

        checked += 1
        gs, ge = p_groups[gi]
        patched_markers = [w for w in p_words[gs:ge] if CHOICE_LO <= w <= CHOICE_HI]
        if patched_markers != pristine_markers:
            issues.append(
                "R%d g%d: marker list changed pristine=%s patched=%s"
                % (
                    res,
                    gi,
                    [hex(m) for m in pristine_markers],
                    [hex(m) for m in patched_markers],
                )
            )
        # group span [gs:ge] -- ge is the FFFF terminator index.
        if ge >= len(p_words) or p_words[ge] != 0xFFFF:
            term = p_words[ge] if ge < len(p_words) else 0xFFFF
            issues.append(
                "R%d g%d: group does not end on FFFF terminator (word=0x%04X)"
                % (res, gi, term)
            )

    if checked == 0:
        raise Skip(
            "no patched choice resource present in build/patched_type2 this run"
        )
    assert not issues, "%d issue(s): %s" % (len(issues), "; ".join(issues[:8]))


# ===========================================================================
# TEST 2 (HARD FAIL): no empty option in injected choice groups
# ===========================================================================
def _split_on_markers(group_words):
    """Yield the content word-list following each FFC0..FFCF marker (in order),
    up to the next marker or the end of the group."""
    options = []
    cur = None
    for w in group_words:
        if CHOICE_LO <= w <= CHOICE_HI:
            if cur is not None:
                options.append(cur)
            cur = []
        elif cur is not None:
            cur.append(w)
    if cur is not None:
        options.append(cur)
    return options


def test_no_empty_injected_option():
    """For INJECTED choice groups (patched group differs from pristine), every
    marker is followed by >=1 content word before the next marker / group end.
    Pristine-kept (still-Japanese) groups are exempt -- only text we re-flowed
    is gated."""
    require_dir(PATCHED_TYPE2_DIR, "run a build first")
    choice_set = build_choice_set()
    if not choice_set:
        raise Skip("CHOICE_SET empty")

    issues = []
    injected = 0
    for res, gi, _pristine_markers in choice_set:
        pg = _patched_groups(res)
        pris = _pristine_groups(res)
        if pg is None or pris is None:
            continue
        p_words, p_groups = pg
        o_words, o_groups = pris
        if gi >= len(p_groups) or gi >= len(o_groups):
            continue
        pgs, pge = p_groups[gi]
        ogs, oge = o_groups[gi]
        patched_group = p_words[pgs:pge]
        pristine_group = o_words[ogs:oge]
        if patched_group == pristine_group:
            continue  # not injected -- still pristine, exempt
        injected += 1
        for oi, opt in enumerate(_split_on_markers(patched_group)):
            # content = words that are not page/line breaks
            content = [w for w in opt if w not in (0xFFFE, 0xFFD2)]
            if not content:
                issues.append(
                    "R%d g%d option %d is EMPTY (no content after its marker)"
                    % (res, gi, oi)
                )

    if injected == 0:
        raise Skip("no injected choice groups in this build")
    assert not issues, "%d empty option(s): %s" % (len(issues), "; ".join(issues[:8]))


# ===========================================================================
# TEST 3 (HARD FAIL): Section-1 integrity on choice resources
# ===========================================================================
def test_section1_integrity():
    """sec1_regression_check on every patched choice resource (protects the
    choice->branch linkage in Section 1)."""
    require_dir(PATCHED_TYPE2_DIR, "run a build first")
    choice_set = build_choice_set()
    if not choice_set:
        raise Skip("CHOICE_SET empty")

    choice_resources = sorted({res for res, _gi, _m in choice_set})
    issues = []
    checked = 0
    for res in choice_resources:
        patched_path = _patched_raw_path(res)
        pristine_path = _pristine_raw_path(res)
        if not os.path.isfile(patched_path):
            continue
        if not os.path.isfile(pristine_path):
            issues.append("R%d: patched present but no pristine extract" % res)
            continue
        pristine = open(pristine_path, "rb").read()
        patched = open(patched_path, "rb").read()
        issues.extend(sec1_regression_check(pristine, patched, "R%d" % res))
        checked += 1

    if checked == 0:
        raise Skip("no patched choice resource present this run")
    assert not issues, "%d issue(s): %s" % (len(issues), "; ".join(issues[:8]))


# ===========================================================================
# TEST 4 (HARD FAIL): global marker-count tripwire
# ===========================================================================
def test_marker_count_tripwire():
    """SUM of patched markers across CHOICE_SET == SUM of pristine markers
    (no net marker loss/gain across the whole build)."""
    require_dir(PATCHED_TYPE2_DIR, "run a build first")
    choice_set = build_choice_set()
    if not choice_set:
        raise Skip("CHOICE_SET empty")

    pristine_total = 0
    patched_total = 0
    checked = 0
    for res, gi, pristine_markers in choice_set:
        pg = _patched_groups(res)
        if pg is None:
            continue  # not rebuilt this run -- exclude from both sums symmetrically
        p_words, p_groups = pg
        if gi >= len(p_groups):
            continue
        checked += 1
        pristine_total += len(pristine_markers)
        gs, ge = p_groups[gi]
        patched_total += sum(
            1 for w in p_words[gs:ge] if CHOICE_LO <= w <= CHOICE_HI
        )

    if checked == 0:
        raise Skip("no patched choice resource present this run")
    assert patched_total == pristine_total, (
        "marker-count drift across %d groups: pristine=%d patched=%d "
        "(net %+d markers -- a choice option was added or lost)"
        % (checked, pristine_total, patched_total, patched_total - pristine_total)
    )


# ===========================================================================
# TEST 5 (WARN, never fails): semantic spot-check
# ===========================================================================
def test_semantic_spotcheck():
    """Decode the patched question + each option for a curated injected sample
    and print them.  Asserts (only for samples that were actually injected) the
    question is non-empty and decoded option count == marker count.  Samples not
    injected are skipped; WARN-only -- this never FAILs the build."""
    if not os.path.isdir(PATCHED_TYPE2_DIR):
        raise Skip("build/patched_type2 missing -- run a build first")

    inspected = 0
    for res, gi in SEMANTIC_SAMPLE:
        pg = _patched_groups(res)
        pris = _pristine_groups(res)
        if pg is None or pris is None:
            print("  [warn] R%d g%d: no patched/pristine -- sample skipped" % (res, gi))
            continue
        p_words, p_groups = pg
        o_words, o_groups = pris
        if gi >= len(p_groups) or gi >= len(o_groups):
            print("  [warn] R%d g%d: group index out of range -- skipped" % (res, gi))
            continue
        pgs, pge = p_groups[gi]
        ogs, oge = o_groups[gi]
        if p_words[pgs:pge] == o_words[ogs:oge]:
            print("  [warn] R%d g%d: not injected (still pristine) -- skipped" % (res, gi))
            continue

        inspected += 1
        group = p_words[pgs:pge]
        # question = everything before the first marker; options follow markers.
        question = []
        for w in group:
            if CHOICE_LO <= w <= CHOICE_HI:
                break
            question.append(w)
        options = _split_on_markers(group)
        marker_count = sum(1 for w in group if CHOICE_LO <= w <= CHOICE_HI)

        q_text = decode_glyphs(question).strip()
        print("  R%d g%d  Q: %r" % (res, gi, q_text))
        for oi, opt in enumerate(options):
            print("    [%d] %r" % (oi, decode_glyphs(opt).strip()))

        # Soft (WARN-only) assertions -- surfaced, never fatal.
        if not q_text:
            print("  [warn] R%d g%d: decoded question is EMPTY" % (res, gi))
        if len(options) != marker_count:
            print(
                "  [warn] R%d g%d: %d decoded options != %d markers"
                % (res, gi, len(options), marker_count)
            )

    if inspected == 0:
        raise Skip("none of the curated samples were injected in this build")
    # WARN-only test: reaching here is a PASS regardless of soft warnings.


# ===========================================================================
# TEST 6 (Tier-3): ISO-level marker integrity
# ===========================================================================
def test_iso_choice_integrity():
    """Re-run TEST 1 + TEST 4 against the resources as they live in the built
    PACKDATA (the real-PS2 path).  Skips cleanly with no ISO."""
    choice_set = build_choice_set()
    if not choice_set:
        raise Skip("CHOICE_SET empty")

    iso = default_iso_path()
    if not os.path.isfile(iso):
        raise Skip("ISO not found: %s (set BUSIN_ISO or build)" % iso)

    # SKIP (don't FAIL) when the on-disc ISO predates the patched_type2 build
    # output: that means no fresh ISO has been built since the choice groups
    # were (re)patched, so the ISO is a stale artifact -- not a regression.
    # Mirrors test_v86_strips._require_fresh_iso.  A freshly built ISO is newer
    # than every patched raw and the comparison runs for real.
    choice_resources = sorted({res for res, _gi, _m in choice_set})
    patched_mtimes = [
        os.path.getmtime(_patched_raw_path(res))
        for res in choice_resources
        if os.path.isfile(_patched_raw_path(res))
    ]
    if patched_mtimes and os.path.getmtime(iso) < max(patched_mtimes):
        raise Skip(
            "ISO %s predates build/patched_type2 -- no fresh ISO built since "
            "the choice groups were patched" % os.path.basename(iso)
        )

    pack = PackData(iso)  # raises Skip itself if no PACKDATA in the ISO

    # group CHOICE_SET by resource
    by_res = {}
    for res, gi, markers in choice_set:
        by_res.setdefault(res, []).append((gi, markers))

    issues = []
    pristine_total = 0
    iso_total = 0
    checked = 0
    try:
        for res in sorted(by_res):
            pris = _pristine_groups(res)
            if pris is None:
                continue
            try:
                data, _tc = pack.extract(res)
                p = parse_type02(data)
                iso_words = p["words"]
                iso_groups, _t = group_offsets(iso_words)
            except Exception as e:
                issues.append("R%d: ISO extract/parse failed: %s" % (res, e))
                continue
            _o_words, o_groups = pris

            if len(iso_groups) != len(o_groups):
                issues.append(
                    "R%d: ISO group_count %d != pristine %d"
                    % (res, len(iso_groups), len(o_groups))
                )
                continue

            for gi, pristine_markers in by_res[res]:
                if gi >= len(iso_groups):
                    issues.append("R%d g%d: out of range in ISO" % (res, gi))
                    continue
                checked += 1
                gs, ge = iso_groups[gi]
                iso_markers = [
                    w for w in iso_words[gs:ge] if CHOICE_LO <= w <= CHOICE_HI
                ]
                # TEST 1 equivalent
                if iso_markers != pristine_markers:
                    issues.append(
                        "R%d g%d: ISO marker list != pristine (%s vs %s)"
                        % (
                            res,
                            gi,
                            [hex(m) for m in iso_markers],
                            [hex(m) for m in pristine_markers],
                        )
                    )
                if ge >= len(iso_words) or iso_words[ge] != 0xFFFF:
                    issues.append("R%d g%d: ISO group not FFFF-terminated" % (res, gi))
                # TEST 4 accumulation
                pristine_total += len(pristine_markers)
                iso_total += len(iso_markers)
    finally:
        pack.close()

    if checked == 0:
        raise Skip("no choice resources resolved from the ISO")
    if iso_total != pristine_total:
        issues.append(
            "ISO marker-count drift: pristine=%d iso=%d (net %+d)"
            % (pristine_total, iso_total, iso_total - pristine_total)
        )
    assert not issues, "%d ISO issue(s): %s" % (len(issues), "; ".join(issues[:8]))


TESTS = [
    test_marker_set_preserved,
    test_no_empty_injected_option,
    test_section1_integrity,
    test_marker_count_tripwire,
    test_semantic_spotcheck,
    test_iso_choice_integrity,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_choice_groups")
