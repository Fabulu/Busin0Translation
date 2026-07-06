#!/usr/bin/env python3
"""
regress_selftest.py -- prove the L1/L2 harness works on REAL existing ramdumps
(no new capture, no emulator).  Run:  python tools/regress_selftest.py

Demonstrations:
  1. png_tripwire flags the BLACK screen (chargenblackscreen.p2s, ~2909 B) and
     PASSES a good frame (RaceSelect.p2s).
  2. pixel_diff between two DIFFERENT good frames shows a large %change; a frame
     against ITSELF shows ~0%.
  3. p2s_extract round-trips ee_ram VA-direct: ee[0x4FED18] is a small mode int
     and ee[0x3A31A0] decodes as a plausible MIPS word.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p2s_extract
import regress_diff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAM = os.path.join(ROOT, "ramdumps")
BLACK = os.path.join(RAM, "chargenblackscreen.p2s")
GOOD1 = os.path.join(RAM, "RaceSelect.p2s")
GOOD2 = os.path.join(RAM, "selectgender.p2s")


def _hr(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    for f in (BLACK, GOOD1, GOOD2):
        if not os.path.isfile(f):
            print("SELF-TEST SKIP: missing fixture %s" % f)
            return 0

    _hr("1. PNG-SIZE TRIPWIRE (catches the post-chargen black screen)")
    rb = regress_diff.png_tripwire(BLACK)
    print("  chargenblackscreen.p2s -> %s" % ("PASS" if rb["ok"] else "FAIL"))
    print("     %s" % rb["reason"])
    rg = regress_diff.png_tripwire(GOOD1)
    print("  RaceSelect.p2s         -> %s" % ("PASS" if rg["ok"] else "FAIL"))
    print("     %s" % rg["reason"])
    assert rb["ok"] is False, "black screen should FAIL the tripwire"
    assert rg["ok"] is True, "good frame should PASS the tripwire"
    # And relative: the black frame vs a good baseline also fails.
    rrel = regress_diff.png_tripwire(BLACK, baseline_p2s=GOOD1)
    print("  black vs good baseline -> %s (%s)"
          % ("PASS" if rrel["ok"] else "FAIL", rrel["reason"]))
    assert rrel["ok"] is False
    print("  ==> TRIPWIRE PROVEN: black flagged, good passes.")

    _hr("2. PIXEL-DIFF (masked framebuffer; catches chargen garble)")
    png1 = p2s_extract.screenshot(GOOD1)
    png2 = p2s_extract.screenshot(GOOD2)
    heat = os.path.join(
        os.environ.get("TEMP", "."), "regress_selftest_heatmap.png")
    r_two = regress_diff.pixel_diff(png1, png2, heatmap_out=heat, masks=[
        # illustrative text-rect masks (chargen sidebar / a lower strip)
        ("upper_strip", 0, 0, 640, 120),
        ("lower_strip", 0, 360, 640, 480),
    ])
    print("  RaceSelect vs selectgender: %.3f%% changed, bbox=%s"
          % (r_two["pct_changed"], r_two["bbox"]))
    print("     per-mask: %s" % {k: round(v, 2) for k, v in r_two["masks"].items()})
    print("     heatmap -> %s" % r_two["heatmap"])
    r_self = regress_diff.pixel_diff(png1, png1)
    print("  RaceSelect vs ITSELF: %.5f%% changed (expect ~0)"
          % r_self["pct_changed"])
    assert r_two["pct_changed"] > 1.0, "two different frames should differ a lot"
    assert r_self["pct_changed"] == 0.0, "a frame vs itself must be 0%"
    print("  ==> PIXEL-DIFF PROVEN: different frames diverge, self==0%.")

    _hr("3. ee_ram VA-DIRECT round-trip")
    ee = p2s_extract.ee_ram(GOOD1)
    print("  len(ee) = %d (expect 33554432)" % len(ee))
    mode = struct.unpack_from("<I", ee, 0x4FED18)[0]
    word = struct.unpack_from("<I", ee, 0x3A31A0)[0]
    op = word >> 26
    print("  ee[0x4FED18] (mode sentinel) = %d  (small int, expect <16)" % mode)
    print("  ee[0x3A31A0] = 0x%08X  (opcode field 0x%02X -> %s)"
          % (word, op, "j/jal (valid MIPS)" if op in (2, 3) else "op 0x%02X" % op))
    assert len(ee) == 33554432
    assert 0 <= mode < 16, "mode sentinel should be a small int"
    assert op in (2, 3), "0x3A31A0 should decode as a j/jal word in these dumps"
    print("  ==> VA-DIRECT PROVEN: RAM==VA reads land on real data.")

    _hr("SELF-TEST RESULT: ALL PROOFS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
