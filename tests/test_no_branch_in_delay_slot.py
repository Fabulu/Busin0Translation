#!/usr/bin/env python3
"""
test_no_branch_in_delay_slot.py -- no PATCHED control transfer may sit in (or
own) a control transfer's delay slot.

RUN-20261011-2104 (v203): Patch 26 hooked 0x3079CC with `j cave`, leaving the
stock `bne v0,v1` at 0x3079D0 in the jump's DELAY SLOT.  A branch/jump in a
delay slot is UNDEFINED on MIPS/R5900: PCSX2 let the jump win, real PS2
hardware does not have to -- a hardware/emulator divergence that every
emulator test passes.  The hook now sits at 0x3079C8 with a plain store in
its delay slot.

This gate scans the built EXE's code segment: for every 4-byte word that
DIFFERS from the pristine EXE, it checks the word's role in both directions:
  * a patched control transfer whose next word (its delay slot) is a control
    transfer, and
  * a patched word sitting in the delay slot of a control transfer.
Either is a failure.  The patched font-table DATA span (Option-E strncpy
tail, from the relocation single source) is excluded.  Pristine-only pairs are the original compiler's
business and are not judged (there are none in practice).
TIER-2: SKIPs when the built/pristine EXE is absent.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402  (relocation single source)

PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")

# .text runs to the end of the dead .text pad that hosts our caves (below the
# battle-heap arena at VA 0x4B0E00); VA = file offset - 0x80 + 0x100000.
CODE_LO_FO = 0x80
CODE_HI_FO = 0x4B0E00 - 0x100000 + 0x80

# Patched DATA inside .text: the Option-E font tables packed into the freed
# tail of the shrunk strncpy (ADV/LSH/ADV2/LSH2 bytes, not instructions).
DATA_SPANS_VA = [
    (RELOC.STRNCPY_VA + len(RELOC.build_strncpy_replacement()),
     RELOC.STRNCPY_VA + RELOC.STRNCPY_ORIG_LEN),
]


def _in_data(va):
    return any(lo <= va < hi for lo, hi in DATA_SPANS_VA)


def _is_cti(w):
    """True if the 32-bit word is a MIPS/R5900 control-transfer instruction
    (has a delay slot): j/jal, jr/jalr, REGIMM branches, beq/bne/blez/bgtz and
    their -likely forms, COP1 bc1x."""
    op = w >> 26
    if op in (0x02, 0x03):                        # j, jal
        return True
    if op == 0x00 and (w & 0x3F) in (0x08, 0x09):  # jr, jalr
        return True
    if op == 0x01 and ((w >> 16) & 0x1F) in (0x00, 0x01, 0x02, 0x03,
                                            0x10, 0x11, 0x12, 0x13):
        return True                               # bltz/bgez(+al)(+l)
    if op in (0x04, 0x05, 0x06, 0x07, 0x14, 0x15, 0x16, 0x17):
        return True                               # beq/bne/blez/bgtz (+l)
    if op == 0x11 and ((w >> 21) & 0x1F) == 0x08:  # bc1f/bc1t(+l)
        return True
    return False


def test_no_patched_branch_in_delay_slot():
    for p in (PRISTINE_EXE, PATCHED_EXE):
        if not os.path.isfile(p):
            raise Skip("%s missing" % os.path.relpath(p, ROOT))
    pr = open(PRISTINE_EXE, "rb").read()
    bd = open(PATCHED_EXE, "rb").read()
    hi = min(CODE_HI_FO, len(pr), len(bd)) - 4
    bad = []
    for fo in range(CODE_LO_FO, hi, 4):
        w0 = struct.unpack_from("<I", bd, fo)[0]
        w1 = struct.unpack_from("<I", bd, fo + 4)[0]
        if not (_is_cti(w0) and _is_cti(w1)):
            continue
        if bd[fo:fo + 8] == pr[fo:fo + 8]:
            continue  # untouched compiler code
        va = fo - 0x80 + 0x100000
        if _in_data(va) or _in_data(va + 4):
            continue  # patched data table, not code
        bad.append("VA 0x%06X: 0x%08X has control transfer 0x%08X in its delay slot"
                   % (va, w0, w1))
    assert not bad, "; ".join(bad[:10])


TESTS = [test_no_patched_branch_in_delay_slot]

if __name__ == "__main__":
    main_exit(TESTS, "test_no_branch_in_delay_slot")
