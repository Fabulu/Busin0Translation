#!/usr/bin/env python3
"""
test_prequel_us_save.py -- US predecessor-save probe retarget gate.

tools/patch_prequel_us_save.py swaps the memory-card "Tale of the Forsaken Land"
bonus probe string from the JP directory BISLPM-62098BUSINWZ to the US directory
BASLUS-20259WIZTFL (SLUS-20259), in place, so the +10 chargen bonus fires from a
US prequel save. Wired into build_v9.py Step 8.45.

Pins:
  1. Pristine EXE holds the stock JP directory string at VA 0x4F95E0 (drift alarm).
  2. Applying the swap yields the US string, NUL-terminated, changing ONLY those
     bytes; and it is idempotent.
  3. The tool ABORTS rather than swap if the stock string isn't found.
  4. The BUILT EXE (when present) carries the US string at the probe site and no
     longer the JP one -- i.e. Step 8.45 ran.

SKIP (not FAIL) when the pristine/built EXE is absent.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import main_exit, require_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import patch_prequel_us_save as P


def test_pristine_has_jp_string():
    require_file(PRISTINE_EXE, "pristine EXE extract")
    d = open(PRISTINE_EXE, "rb").read()
    assert d[P.STR_FO:P.STR_FO + 19] == P.JP, \
        "stock JP directory string missing @0x%X (address drift?)" % P.STR_VA


def test_swap_is_surgical_and_idempotent():
    require_file(PRISTINE_EXE, "pristine EXE extract")
    import tempfile
    src = open(PRISTINE_EXE, "rb").read()
    with tempfile.TemporaryDirectory() as td:
        a = os.path.join(td, "in.bin")
        b = os.path.join(td, "out.bin")
        open(a, "wb").write(src)
        P.apply(a, b)
        out = open(b, "rb").read()
        # US string present and NUL-terminated
        assert out[P.STR_FO:P.STR_FO + 18] == P.US
        assert out[P.STR_FO + 18] == 0
        # ONLY the 19-byte string slot changed
        diff = [i for i in range(len(src)) if src[i] != out[i]]
        assert diff and min(diff) >= P.STR_FO and max(diff) < P.STR_FO + 19, \
            "swap touched bytes outside the string slot: %r" % diff[:8]
        # idempotent
        c = os.path.join(td, "out2.bin")
        open(a, "wb").write(out)
        P.apply(a, c)
        assert open(c, "rb").read() == out, "second application changed bytes"


def test_aborts_when_stock_string_absent():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        a = os.path.join(td, "junk.bin")
        # a buffer big enough to reach the offset, without the JP string there
        open(a, "wb").write(b"\x00" * (P.STR_FO + 64))
        raised = False
        try:
            P.apply(a, os.path.join(td, "o.bin"))
        except SystemExit:
            raised = True
        assert raised, "tool must ABORT when the stock JP string is not at the probe site"


def test_built_exe_retargeted_if_present():
    if not os.path.exists(PATCHED_EXE):
        return
    d = open(PATCHED_EXE, "rb").read()
    assert d[P.STR_FO:P.STR_FO + 18] == P.US, \
        "BUILT EXE probe string is not US BASLUS-20259WIZTFL -- Step 8.45 did not run"
    assert d[P.STR_FO:P.STR_FO + 19] != P.JP


TESTS = [
    test_pristine_has_jp_string,
    test_swap_is_surgical_and_idempotent,
    test_aborts_when_stock_string_absent,
    test_built_exe_retargeted_if_present,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_prequel_us_save")
