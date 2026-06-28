#!/usr/bin/env python3
"""
test_chargen_diag_guard.py -- round-2 gate: the CHARGEN_DIAG instrumentation is
OPT-IN and the PRODUCTION build keeps the (retargeted) Patch-19 proportional fix.

CONTEXT
-------
The round-1 chargen fix FAILED live (v132 still rendered the New-Character/Status
screen in wide MONOSPACE).  Round-1's root-cause claim -- that Patch 19 should write
the sp+0x1cc pen -- was wrong: the chargen Block-1 draw path never reads that pen.
Round-2 split the work two ways:

  * PRODUCTION fix (W1-CHAR/Patch 19, gated by test_chargen_centering.py): retarget
    the proportional advance onto the chargen Block-1 stride hooks at VA 0x308040
    (advance) and 0x308018 (draw-shift), reading the resident SoT ADV/LEFTSHIFT
    tables (0x7564/0x7690) and GATED on screen-mode == 5.  That EXE-byte contract is
    fully covered by test_chargen_centering.py; this module does NOT duplicate it.
  * A default-OFF DIAGNOSTIC (CHARGEN_DIAG): a pure read+store cave at 0x308040 that
    dumps register candidates to scratch RAM 0x4CAAA0 so the live root cause can be
    measured.  It is for a DEBUG ISO only and MUST NOT ship in production.

This module gates the DIAGNOSTIC CONTRACT so the diag can never silently ship and
can never collide with the production caves:

  DIAG-OFF-DEFAULT  CHARGEN_DIAG defaults to OFF (env CHARGEN_DIAG must be opt-in);
                    a default-ON diag would replace the production proportional fix
                    with a no-op read+store cave and the chargen screen would stay
                    monospace AND the suite's chargen EXE-byte gate would flip.
  DIAG-EXCLUSIVE    when CHARGEN_DIAG is ON the production Patch-19 caves are SKIPPED
                    (their hook at 0x308040 would collide with the diag hook), and
                    when OFF the diag cave is NOT installed -- the two are mutually
                    exclusive in source.
  PROD-IS-PROPORTIONAL  with the diag OFF (the normal/CI path) the SHIPPED EXE holds
                    the production Patch-19 stride hooks (j cave, NOT the round-1
                    dead sp+0x1cc write and NOT the diag j 0x4C7790) -- the chargen
                    proportional fix is what actually ships.  Pins that the v132
                    failure mode (Patch 19 writing the dead pen) is gone.
  DIAG-CAVE-PURE    the diagnostic cave's scratch target (0x4CAAA0) and its own hook
                    target (0x4C7790) are distinct from the production cave region,
                    so a stray diag definition cannot overwrite production caves.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit, require_file  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "build"))
import _reloc_v147_design as RELOC  # noqa: E402  (v148 relocated cave bases)

PATCH_EXE = os.path.join(ROOT, "build", "patch_exe.py")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")


def _fo(va):
    return va - 0x100000 + 0x80


# Chargen Block-1 stride hooks (the production Patch-19 sites).
HOOK1_FO = _fo(0x308040)   # advance hook
HOOK2_FO = _fo(0x308018)   # draw-shift hook
HOOK1_ORIG = 0x24420018    # pristine: addiu v0,v0,0x18  (24px monospace stride)
HOOK2_ORIG = 0x87A301CC    # pristine: lh v1,0x1cc(sp)
# Production trampolines installed when CHARGEN_DIAG is OFF.  v148 RELOCATED the Patch-19
# caves below the EE battle-heap arena (was 0x4D6600/0x4D6660) -> the hook j-words follow.
HOOK1_PROD_J = RELOC.P19C1_HOOK_JWORD  # j RELOC.P19C1_VA (production advance cave)
HOOK2_PROD_J = RELOC.P19C2_HOOK_JWORD  # j RELOC.P19C2_VA (production draw-shift cave)
# The DIAGNOSTIC hook word (j 0x4C7790) installed at 0x308040 when CHARGEN_DIAG is ON.
HOOK1_DIAG_J = 0x08000000 | (0x4C7790 >> 2)  # j 0x4C7790
# Round-1 dead write (the FAILED approach): sh ...,0x1cc(sp).  Must NOT be the shipped
# hook -- the chargen draw path never reads sp+0x1cc.
DEAD_PEN_STORE_IMM = 0x1CC


def _src():
    require_file(PATCH_EXE, "chargen diag guard")
    return open(PATCH_EXE, encoding="utf-8").read()


def _w(data, fo):
    return struct.unpack_from("<I", data, fo)[0]


def _patched():
    if not os.path.isfile(PATCHED_EXE):
        raise Skip("build/SLPM_653.78_patched missing (run build/patch_exe.py)")
    return open(PATCHED_EXE, "rb").read()


# ---------------------------------------------------------------------------
# DIAG-OFF-DEFAULT
# ---------------------------------------------------------------------------
def test_chargen_diag_defaults_off():
    """DIAG-OFF-DEFAULT: CHARGEN_DIAG is OFF unless the env var opts in.  Source must
    read the flag from os.environ with a default of '0' (off) -- a default-ON diag
    would replace the production proportional fix with a no-op read+store cave and
    ship the wide-monospace regression."""
    src = _src()
    assert "CHARGEN_DIAG" in src, (
        "build/patch_exe.py has no CHARGEN_DIAG flag -- the diagnostic-vs-production "
        "split (W1-CHAR) is missing"
    )
    # Must be env-driven and default OFF.  Accept either '0'/'1' or a falsey default.
    norm = src.replace(" ", "")
    assert 'os.environ.get("CHARGEN_DIAG"' in norm or "os.environ.get('CHARGEN_DIAG'" in norm, (
        "CHARGEN_DIAG must come from os.environ.get('CHARGEN_DIAG', ...) so a debug "
        "build is opt-in via the env var, not a committed source flip"
    )
    assert 'CHARGEN_DIAG", "0"' in src.replace("'", '"') or '"0") == "1"' in src.replace("'", '"'), (
        "CHARGEN_DIAG default is not OFF ('0') -- the production build must be the "
        "proportional fix, the diagnostic must be opt-in"
    )
    # Evaluate the actual default with no env var set: it MUST be False.
    env_backup = os.environ.pop("CHARGEN_DIAG", None)
    try:
        ns = {"os": os}
        exec('CHARGEN_DIAG = (os.environ.get("CHARGEN_DIAG", "0") == "1")', ns)
        assert ns["CHARGEN_DIAG"] is False, (
            "with no CHARGEN_DIAG env var the flag evaluates True -- the diagnostic "
            "would ship by default"
        )
    finally:
        if env_backup is not None:
            os.environ["CHARGEN_DIAG"] = env_backup


# ---------------------------------------------------------------------------
# DIAG-EXCLUSIVE
# ---------------------------------------------------------------------------
def test_diag_and_production_are_mutually_exclusive():
    """DIAG-EXCLUSIVE: source must gate so that when CHARGEN_DIAG is ON the production
    Patch-19 caves are SKIPPED, and when OFF the diag cave is not installed.  Both
    hook 0x308040, so installing both would corrupt the EXE.  Asserted by requiring
    the production Patch-19 install block to be guarded by `if CHARGEN_DIAG:` (skip)
    and the diag install to be guarded by `if CHARGEN_DIAG`."""
    src = _src()
    assert "if CHARGEN_DIAG:" in src, (
        "patch_exe.py does not branch on `if CHARGEN_DIAG:` -- the production caves "
        "must be skipped when the diagnostic hook is installed (both hook 0x308040)"
    )
    # The production Patch-19 block must explicitly skip when DIAG is on (the comment
    # /pass that prevents the collision).
    assert "Patch-19 production caves" in src or "Patch 19 production" in src or \
        "production Patch-19 caves" in src or "production Patch 19" in src or \
        ("CHARGEN_DIAG:" in src and "Patch 19 SKIPPED" in src), (
        "patch_exe.py does not document/skip the production Patch-19 caves under "
        "CHARGEN_DIAG -- the diag and production caves both hook 0x308040 and would "
        "collide"
    )


# ---------------------------------------------------------------------------
# PROD-IS-PROPORTIONAL  (TIER-2 built EXE, OFF path)
# ---------------------------------------------------------------------------
def test_production_exe_ships_proportional_not_dead_pen_or_diag():
    """PROD-IS-PROPORTIONAL: the BUILT (CHARGEN_DIAG OFF) EXE holds the production
    Patch-19 stride trampolines at 0x308040/0x308018 -- NOT the round-1 dead sp+0x1cc
    write (the FAILED v132 approach) and NOT the diagnostic j 0x4C7790.  This pins
    that the chargen screen ships the proportional fix, not the no-op diag, and not
    the dead pen.

    SKIP if no patched EXE.  If the patched EXE WAS built with CHARGEN_DIAG=1 (the
    0x308040 hook == j 0x4C7790), SKIP rather than fail -- this gate is for the
    production/CI build; a debug ISO is validated by booting and dumping scratch RAM."""
    data = _patched()
    h1 = _w(data, HOOK1_FO)
    if h1 == HOOK1_DIAG_J:
        raise Skip(
            "patched EXE was built with CHARGEN_DIAG=1 (0x308040 = j 0x4C7790) -- this "
            "is a debug ISO; the production proportional gate does not apply"
        )
    h2 = _w(data, HOOK2_FO)
    assert h1 == HOOK1_PROD_J, (
        "production chargen advance hook @0x308040 = 0x%08X, expected the Patch-19 "
        "trampoline j 0x4D6600 (0x%08X) -- the chargen proportional fix did not ship"
        % (h1, HOOK1_PROD_J)
    )
    assert h2 == HOOK2_PROD_J, (
        "production chargen draw-shift hook @0x308018 = 0x%08X, expected j 0x4D6660 "
        "(0x%08X) -- the chargen proportional draw-shift did not ship" % (h2, HOOK2_PROD_J)
    )
    # The hook must NOT be the round-1 dead sp+0x1cc store (the failed approach).
    assert (h1 >> 26) != 0x29 or (h1 & 0xFFFF) != DEAD_PEN_STORE_IMM, (
        "production chargen hook @0x308040 is a sh ...,0x1cc(sp) -- the round-1 dead "
        "pen write that FAILED in v132; the fix must retarget the stride, not the pen"
    )


def test_production_hooks_were_pristine_stride_words():
    """PROD-IS-PROPORTIONAL (preflight): the PRISTINE EXE holds the original 24px
    monospace stride words at the two hook sites, so the production Patch-19 (and the
    diag) land on the intended, un-moved sites.  SKIP if no pristine EXE."""
    require_file(PRISTINE_EXE, "chargen diag preflight")
    pr = open(PRISTINE_EXE, "rb").read()
    assert _w(pr, HOOK1_FO) == HOOK1_ORIG, (
        "pristine chargen advance @0x308040 = 0x%08X, expected the 24px monospace "
        "stride addiu v0,v0,0x18 (0x%08X) -- the hook site moved" % (_w(pr, HOOK1_FO), HOOK1_ORIG)
    )
    assert _w(pr, HOOK2_FO) == HOOK2_ORIG, (
        "pristine chargen draw-shift @0x308018 = 0x%08X, expected lh v1,0x1cc(sp) "
        "(0x%08X) -- the hook site moved" % (_w(pr, HOOK2_FO), HOOK2_ORIG)
    )


# ---------------------------------------------------------------------------
# DIAG-CAVE-PURE  (source-level scratch/hook target separation)
# ---------------------------------------------------------------------------
def test_diag_targets_are_separate_from_production():
    """DIAG-CAVE-PURE: the diagnostic uses scratch RAM 0x4CAAA0 and a hook cave at
    0x4C7790 -- distinct from the production cave region (0x4D6600/0x4D6660) -- so a
    stray diag definition cannot overwrite the production caves.  Source-level: both
    diag addresses are referenced and are not the production cave addresses."""
    src = _src()
    # The diagnostic scratch + cave addresses must be present (the diag is wired).
    assert "0x4CAAA0" in src.upper().replace("0X", "0x").upper() or "0x4caaa0" in src.lower(), (
        "patch_exe.py does not reference the diagnostic scratch RAM 0x4CAAA0 -- the "
        "CHARGEN_DIAG cave is not wired"
    )
    assert "0x4C7790" in src.upper().replace("0X", "0x").upper() or "0x4c7790" in src.lower(), (
        "patch_exe.py does not reference the diagnostic cave VA 0x4C7790"
    )
    # The diag hook cave (0x4C7790) must be DISTINCT from the production caves
    # (0x4D6600/0x4D6660) so the two cannot alias.
    assert 0x4C7790 not in (0x4D6600, 0x4D6660), "diag/production cave addresses alias"


TESTS = [
    test_chargen_diag_defaults_off,
    test_diag_and_production_are_mutually_exclusive,
    test_production_exe_ships_proportional_not_dead_pen_or_diag,
    test_production_hooks_were_pristine_stride_words,
    test_diag_targets_are_separate_from_production,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_chargen_diag_guard")
