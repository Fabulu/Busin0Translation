#!/usr/bin/env python3
"""
test_pipeline_rules.py -- static guards on the build pipeline source.

Locks in the v85 pipeline decisions so they cannot silently regress:
  * BUG-3: Steps 3.6/3.7 (patch_r1188_comprehensive / patch_r1188_bw256) must
    stay DISABLED -- R1188 is the live dialogue/narration font and those
    patchers corrupt ~150 live glyph cells (the r/y/V artifacts).
  * BUG-1: the word-grid pattern-matching mechanism (MULTI_WORD_OPCODES /
    body_positions) must NEVER return to tools/patch_section1_offsets.py.
  * R34: the empirically verified group->message mapping mi = gi - 1 (with
    the gi==0 structural-table skip) must stay in build_v9.py Step 2.
  * Stale-artifact hygiene: Step 4 must purge build/patched_type2 before
    injecting (so walk-skipped resources ship pristine).
  * TIER 2: after a build, build/packdata_resources must NOT contain
    1188_type01.raw (rebuild_packdata falls back to the pristine raw).
  * TIER 2: R35's header + offset table (bytes 0x00..0x85) must survive the
    Step 2 in-place injection byte-identical (the v85 'Save'-over-header bug).
"""

import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    BUILD_V9,
    PACKDATA_RES_DIR,
    RAW_DIR,
    ROOT,
    SEC1_PATCHER,
    Skip,
    main_exit,
    require_file,
)


def _source(path):
    require_file(path, "pipeline source")
    return open(path, encoding="utf-8").read()


def _strip_inline_comments(src):
    """Drop the trailing '#...' from every line so doc comments cannot trip a scan."""
    return "\n".join(line.split("#", 1)[0] for line in src.splitlines())


def _active_lines(src):
    """Yield (lineno, line) for lines that are not pure comments."""
    for i, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            yield i, line


def test_r1188_patchers_disabled():
    src = _source(BUILD_V9)
    offenders = []
    for lineno, line in _active_lines(src):
        # Strip any trailing comment, then look for the forbidden calls in code
        code = line.split("#", 1)[0]
        if "patch_r1188_comprehensive" in code or "patch_r1188_bw256" in code:
            offenders.append("line %d: %s" % (lineno, line.strip()))
    assert not offenders, (
        "build_v9.py re-enables the R1188 patchers (BUG-3: they corrupt ~150 "
        "live dialogue-font glyph cells): %s" % "; ".join(offenders)
    )
    # The pipeline must also actively remove any stale 1188 override.
    assert "1188_type01.raw" in src, (
        "build_v9.py no longer references 1188_type01.raw -- the stale-override "
        "deletion (pristine fallback) appears to be gone"
    )


def test_no_pattern_matching_in_sec1_patcher():
    src = _source(SEC1_PATCHER)
    for ident in ("MULTI_WORD_OPCODES", "body_positions"):
        assert ident not in src, (
            "tools/patch_section1_offsets.py contains %r -- the v83/v84 "
            "word-grid pattern-matching mechanism must never come back; "
            "Section 1 is byte-addressed and must be disassembled" % ident
        )
    # The patcher must keep using the disassembler.
    assert "sec1_disasm" in src, (
        "patch_section1_offsets.py no longer imports sec1_disasm -- "
        "Section 1 patching must stay walk-based"
    )


def test_r34_mapping_rule():
    src = _source(BUILD_V9)
    assert re.search(r"\bmi\s*=\s*gi\s*-\s*1\b", src), (
        "build_v9.py Step 2 lost the R34 mapping rule 'mi = gi - 1' "
        "(empirically verified group->message alignment)"
    )
    assert re.search(r"\bgi\s*==\s*0\b", src), (
        "build_v9.py Step 2 lost the R34 group-0 skip -- group 0 is a "
        "STRUCTURAL TABLE, writing text there corrupts item lookups"
    )


def test_patched_type2_purge_present():
    src = _source(BUILD_V9)
    has_purge = re.search(
        r"glob\.glob\(\s*['\"]build/patched_type2/\*\.raw['\"]\s*\)", src
    )
    assert has_purge, (
        "build_v9.py Step 4 no longer purges build/patched_type2/*.raw -- "
        "stale corrupted files from older builds would be merged in Step 6"
    )


def test_r1188_override_absent_in_build_output():
    """TIER 2: a finished build must NOT carry a 1188 override file."""
    if not os.path.isdir(PACKDATA_RES_DIR) or not os.listdir(PACKDATA_RES_DIR):
        raise Skip("build/packdata_resources empty/missing (run a build first)")
    override = os.path.join(PACKDATA_RES_DIR, "1188_type01.raw")
    assert not os.path.exists(override), (
        "build/packdata_resources/1188_type01.raw EXISTS -- R1188 (the live "
        "dialogue font) would ship patched instead of pristine (BUG-3)"
    )


def test_r35_header_intact_in_build_output():
    """TIER 2: R35's header + offset table must survive Step 2 untouched.

    R35 (0035_type02.raw) has a 0x20-byte header plus a 25-entry offset table
    ending at 0x86 (BE u16 count at 0x20, ascending BE u32s).  The v85 bug
    wrote translation message 1 ('Save') over bytes 0x00..0x85 because Step 2
    scanned FFFF groups from byte 0.  Bytes 0x00..0x85 of the build output
    must be byte-identical to the pristine extracted raw.
    (Empirical layout: build/recon_v85/qa/r35_alignment_check.py)
    """
    built = os.path.join(PACKDATA_RES_DIR, "0035_type02.raw")
    if not os.path.isfile(built):
        raise Skip("build/packdata_resources/0035_type02.raw missing (run a build first)")
    pristine = require_file(
        os.path.join(RAW_DIR, "0035_type02.raw"), "R35 pristine raw"
    )
    with open(pristine, "rb") as fh:
        want = fh.read(0x86)
    with open(built, "rb") as fh:
        got = fh.read(0x86)
    assert got == want, (
        "R35 build output bytes 0x00..0x85 (header + offset table) differ "
        "from the pristine raw -- the v85 'Save'-over-header corruption "
        "(Step 2 must scan FFFF groups from 0x86, mapping mi = gi - 1)"
    )


def test_metrics_single_source():
    """Every width-bearing build step must read tools/glyph_metrics.py -- the
    single source of truth for per-glyph advance/left-shift.  A step that
    recomputes widths inline silently desyncs the shipped EXE cave tables from
    the wrap/centering budget (this project's #1 bug).  This asserts the POSITIVE
    (the import is present); the NEGATIVE inline-recompute scan lives in
    test_glyph_metrics_sync.test_g2_no_inline_width_recompute -- keep them split
    so the two guards never drift."""
    patch_exe = os.path.join(os.path.dirname(BUILD_V9), "patch_exe.py")
    src = _source(patch_exe)
    assert "import glyph_metrics" in src, (
        "build/patch_exe.py no longer imports glyph_metrics -- the EXE "
        "proportional-spacing caves (advance LUT + draw-shift, Patch 14) would "
        "compute widths from an inline copy, silently desyncing from the build "
        "wrap + centering + test gates (the #1 desync bug)"
    )
    # A build step is forbidden from writing a raw 256-byte advance literal
    # (bytearray([0x12]) * 256) unless it sources the table from glyph_metrics.
    # That literal is the diagnostic-only pattern; in a shipping step it MUST come
    # from glyph_metrics.adv_table_256().  Diagnostics are whitelisted (they
    # intentionally inline tables for A/B bring-up before Stage-0 promotion).
    # TODO(P2/Stage-0): when apply_prop_diag2.py's caves are promoted into
    #   patch_exe.py, DELETE the diagnostics and drop this whitelist.
    DIAG_WHITELIST = {"apply_prop_diag.py", "apply_prop_diag2.py"}
    raw_adv = re.compile(r"bytearray\(\s*\[\s*0x12\s*\]\s*\)\s*\*\s*256")
    for path in sorted(glob.glob(os.path.join(ROOT, "build", "*.py"))):
        base = os.path.basename(path)
        if base in DIAG_WHITELIST:
            continue
        code = _strip_inline_comments(_source(path))
        if raw_adv.search(code):
            assert "glyph_metrics" in _source(path), (
                "%s writes a raw 256-byte advance table without importing "
                "glyph_metrics -- promote it to glyph_metrics.adv_table_256() "
                "or whitelist it as a diagnostic" % base
            )


TESTS = [
    test_r1188_patchers_disabled,
    test_no_pattern_matching_in_sec1_patcher,
    test_r34_mapping_rule,
    test_patched_type2_purge_present,
    test_r1188_override_absent_in_build_output,
    test_r35_header_intact_in_build_output,
    test_metrics_single_source,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_pipeline_rules")
