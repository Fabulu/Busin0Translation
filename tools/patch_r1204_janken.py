#!/usr/bin/env python3
"""patch_r1204_janken -- restore the Janken Man "trembling tell" (issue #26).

THE BUG (byte-proven): the Janken minigame's reveal-chant has three visually
distinct variants in pristine R1204, distinguished by ONE embedded control token
sitting immediately before the last glyph:

    G185 = "guu-choki-paa ...jaaan"           (carries FB03, the mode token)
    G186 = FB03 <ja~>       FB04  <n>          <- reveal variant B
    G187 = FB03 <ja~>       FB05  <n>          <- reveal variant C

FB04 / FB05 drive the on-screen "tremble" that tells the player which throw is
coming -- the whole point of the minigame's tell. Our English injection
(tools/inject_type2_dialogue.py PLAIN PATH: new_group = leading + eng + trailing)
preserves only *leading/trailing* contiguous control runs, so it swallowed the
*interior* FB04/FB05 when it replaced the text. Built G186 and G187 both collapsed
to the SAME bytes:

    FB03 + "Shoooot" (S h o o o o t) + "!"     (glyph = ascii - 0x20; ! = 0x0001)

Three distinguishable reveals became two (G185 vs G186==G187), so the tell is
unreadable. Confirmed by the control-token census (FB04 19->18, FB05 3->2) while
the choice-menu markers FFC0/FFC1/FFC2 in G188 are untouched. This is our
text-data regression -- fixable purely in PACKDATA, works on real PS2 hardware.

THE FIX (size-neutral, offset-safe): rewrite the two collapsed 9-word groups
IN PLACE, dropping one redundant 'o' and putting the tremble token back in the
second-to-last slot (mirroring pristine's placement before the final glyph):

    G186: FB03 S h o o o o t !   ->   FB03 S h o o o t FB04 !   ("Shooot!" + tremble)
    G187: FB03 S h o o o o t !   ->   FB03 S h o o o t FB05 !

Both stay exactly 9 words / 18 bytes, so NO Section-2 offset shifts and NO
Section-1 offset re-patching is needed (an insertion would have grown the group
and desynced every downstream group offset the type-2 injector already computed).

Input/Output: build/packdata_resources/1204_type02.raw (in place). Runs in
build/build_v9.py Step 6.5, after the type-2 injection + Step 6 merge produce the
English R1204 and before Step 7 rebuild_packdata. Gated by tests/test_janken_tremble.py.
"""
import os
import struct
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R1204 = os.path.join(BASE, "build", "packdata_resources", "1204_type02.raw")

# Section-2 header fields (little-endian).
SEC2_SIZE_OFF = 0x14
SEC2_OFF_OFF = 0x18
N_GROUPS = 999  # pristine and built both have 999 FFFF-groups

# FFFF-group indices in Section 2.
G_CHANT = 185  # anchor: the FB03 chant group, must stay intact
G_VAR_B = 186  # reveal variant B -- pristine had FB04 before the last glyph
G_VAR_C = 187  # reveal variant C -- pristine had FB05 before the last glyph

FB03, FB04, FB05 = 0xFB03, 0xFB04, 0xFB05

# The COLLAPSED pre-image our English injection produces for BOTH 186 and 187:
# FB03 + "Shoooot" + "!" (0x33='S' 0x48='h' 0x4F='o' 0x54='t' 0x01='!').
PREIMAGE = (FB03, 0x0033, 0x0048, 0x004F, 0x004F, 0x004F, 0x004F, 0x0054, 0x0001)


def _restored(token):
    # Size-neutral: drop one 'o', token in the second-to-last slot (before '!').
    return (FB03, 0x0033, 0x0048, 0x004F, 0x004F, 0x004F, 0x0054, token, 0x0001)


def fail(msg):
    print(f"FATAL(patch_r1204_janken): {msg}")
    sys.exit(1)


def parse_groups(blob):
    """Return [(index, start_byte, [words])] for FFFF-delimited Section-2 groups."""
    sec2_size = struct.unpack_from("<I", blob, SEC2_SIZE_OFF)[0]
    sec2_off = struct.unpack_from("<I", blob, SEC2_OFF_OFF)[0]
    end = min(sec2_off + sec2_size, len(blob))
    out, words = [], []
    gi, start, pos = 0, sec2_off, sec2_off
    while pos + 2 <= end:
        w = struct.unpack_from(">H", blob, pos)[0]
        if w == 0xFFFF:
            out.append((gi, start, words))
            gi += 1
            words = []
            start = pos + 2
        else:
            words.append(w)
        pos += 2
    return out


def main():
    print("--- patch_r1204_janken: restore Janken tremble tell (FB04/FB05) ---")
    if not os.path.exists(R1204):
        fail(f"missing {R1204} (Step 4 type-2 injection + Step 6 merge must run first)")
    data = bytearray(open(R1204, "rb").read())
    orig = bytes(data)

    groups = parse_groups(data)
    if len(groups) != N_GROUPS:
        fail(f"expected {N_GROUPS} Section-2 groups, found {len(groups)} -- R1204 layout changed")
    gd = {gi: (start, words) for gi, start, words in groups}

    # Anchor: chant group 185 must still be a live FB03 group (indices unshifted).
    if G_CHANT not in gd or FB03 not in gd[G_CHANT][1]:
        fail(f"group {G_CHANT} is not the expected FB03 chant group -- group indices shifted?")

    for gi, token in ((G_VAR_B, FB04), (G_VAR_C, FB05)):
        start, words = gd[gi]
        if tuple(words) != PREIMAGE:
            fail(
                f"group {gi} != expected collapsed 'Shoooot' pre-image (got "
                f"{[hex(w) for w in words]}). The English text for R1204 msg{gi} "
                f"changed -- re-derive the restored group before patching."
            )
        new_words = _restored(token)
        assert len(new_words) == len(words), "restored group must be size-neutral"
        struct.pack_into(">%dH" % len(new_words), data, start, *new_words)

    # ---- verification + diff containment ----
    g2 = {gi: words for gi, _s, words in parse_groups(data)}
    if FB04 not in g2[G_VAR_B]:
        fail("group 186 missing FB04 after patch")
    if FB05 not in g2[G_VAR_C]:
        fail("group 187 missing FB05 after patch")
    if g2[G_VAR_B] == g2[G_VAR_C]:
        fail("groups 186/187 still identical after patch -- tell not restored")

    if len(data) != len(orig):
        fail("size changed -- must be a size-neutral in-place edit")
    allowed = set()
    for gi in (G_VAR_B, G_VAR_C):
        s = gd[gi][0]
        allowed |= set(range(s, s + len(PREIMAGE) * 2))
    diffs = [i for i in range(len(orig)) if orig[i] != data[i]]
    stray = [i for i in diffs if i not in allowed]
    if stray:
        fail(f"diff containment violated (bytes outside G186/G187): {[hex(i) for i in stray[:8]]}")

    with open(R1204, "wb") as f:
        f.write(data)
    print("  G186: Shoooot! -> Shooot!+FB04   G187: Shoooot! -> Shooot!+FB05")
    print(f"  {len(diffs)} bytes changed (in-place, size-neutral) -> {R1204}")


if __name__ == "__main__":
    main()
