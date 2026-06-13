#!/usr/bin/env python3
"""
test_patch_section1.py -- the Section-1 offset patcher (BUG-1/BUG-2 fix).

TIER 1: runs inject_and_patch() on pristine R1198 with a tiny synthetic
translation dict into a tempfile directory and asserts the three v85
guarantees (re-walk OK, FFFF invariant, Section-1 diffs confined to walked
operand ranges).  Also asserts the walk-failure fallback: R989 must return
(None, 'sec1 walk failed ...') and write NOTHING.

TIER 2: applies the same three assertions to EVERY build/patched_type2/*.raw
present from the last build.  This is the build-output regression gate --
the v84 pattern-matching corruption would fail it instantly.
"""

import glob
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import (
    PATCHED_TYPE2_DIR,
    RAW_DIR,
    Skip,
    encode_english,
    get_disasm,
    main_exit,
    require_file,
    sec1_regression_check,
    start_correctness_issues,
)


def _import_patcher():
    get_disasm()  # Skip cleanly when the opcode table is missing
    try:
        from patch_section1_offsets import inject_and_patch
    except ImportError as e:
        raise Skip("tools/patch_section1_offsets.py not importable: %s" % e)
    return inject_and_patch


def test_inject_r1198_synthetic():
    """Synthetic end-to-end injection on R1198 (small) into a temp dir."""
    inject_and_patch = _import_patcher()
    require_file(os.path.join(RAW_DIR, "1198_type02.raw"), "pristine extract")

    msg_trans = {
        2: encode_english("hello regression test"),
        5: encode_english("first line") + [0xFFFE] + encode_english("second line"),
        7: encode_english("x"),  # extreme shrink
    }
    tmp = tempfile.mkdtemp(prefix="busin_test_r1198_")
    try:
        out_name, status = inject_and_patch(1198, msg_trans, RAW_DIR, tmp)
        assert out_name == "1198_type02.raw", (
            "inject_and_patch failed: %s" % status
        )
        out_path = os.path.join(tmp, out_name)
        assert os.path.isfile(out_path), "output file not written"
        assert os.path.getsize(out_path) % 2048 == 0, "output not sector-padded"

        pristine = open(os.path.join(RAW_DIR, "1198_type02.raw"), "rb").read()
        patched = open(out_path, "rb").read()
        issues = sec1_regression_check(pristine, patched, "R1198(synthetic)")
        assert not issues, "; ".join(issues[:5])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_walk_failure_fallback_r989():
    """R989 (binary VIF data) must be skipped: (None, 'sec1 walk failed...')
    and NO output file written -- the resource ships pristine."""
    inject_and_patch = _import_patcher()
    require_file(os.path.join(RAW_DIR, "0989_type02.raw"), "pristine extract")

    tmp = tempfile.mkdtemp(prefix="busin_test_r989_")
    try:
        out_name, status = inject_and_patch(989, {0: [1, 2, 3]}, RAW_DIR, tmp)
        assert out_name is None, (
            "R989 was NOT skipped (returned %r) -- binary data would be "
            "corrupted and shipped" % out_name
        )
        assert "sec1 walk failed" in status, (
            "unexpected skip reason: %r" % status
        )
        leftovers = os.listdir(tmp)
        assert not leftovers, "files written despite walk failure: %s" % leftovers
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_build_outputs_regression_gate():
    """TIER 2: every *.raw in build/patched_type2 passes re-walk + FFFF
    invariant + diff confinement against its pristine counterpart."""
    files = sorted(glob.glob(os.path.join(PATCHED_TYPE2_DIR, "*.raw")))
    if not files:
        raise Skip("no build outputs in build/patched_type2 (run a build first)")
    get_disasm()

    all_issues = []
    checked = 0
    for f in files:
        name = os.path.basename(f)
        pris_path = os.path.join(RAW_DIR, name)
        if not os.path.isfile(pris_path):
            all_issues.append("%s: no pristine counterpart in extracted/packdata_raw" % name)
            continue
        pristine = open(pris_path, "rb").read()
        patched = open(f, "rb").read()
        all_issues.extend(sec1_regression_check(pristine, patched, name))
        all_issues.extend(start_correctness_issues(pristine, patched, name))
        checked += 1
    assert checked > 0, "no patched files could be checked"
    assert not all_issues, (
        "%d issue(s) across %d build outputs: %s"
        % (len(all_issues), checked, "; ".join(all_issues[:8]))
    )


def test_start_offset_correct():
    """An empty-translation injection of R1196 must preserve every 0x04 START:
    rel==0 starts stay pinned to the new group start; mid-group (name-island)
    starts stay inside the same group and point at real content.  Guards any
    future patcher change that pushes a start past the intended group beginning
    (the FFFF-end gate alone would not catch leading truncation)."""
    inject_and_patch = _import_patcher()
    pris_path = require_file(
        os.path.join(RAW_DIR, "1196_type02.raw"), "pristine extract"
    )

    tmp = tempfile.mkdtemp(prefix="busin_test_start_r1196_")
    try:
        out_name, status = inject_and_patch(1196, {}, RAW_DIR, tmp)
        assert out_name == "1196_type02.raw", (
            "inject_and_patch(1196, {}) failed: %s" % status
        )
        out_path = os.path.join(tmp, out_name)
        assert os.path.isfile(out_path), "output file not written"

        pristine = open(pris_path, "rb").read()
        patched = open(out_path, "rb").read()
        issues = start_correctness_issues(pristine, patched, "R1196")
        assert not issues, "; ".join(issues[:8])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TESTS = [
    test_inject_r1198_synthetic,
    test_walk_failure_fallback_r989,
    test_start_offset_correct,
    test_build_outputs_regression_gate,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_patch_section1")
