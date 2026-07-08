#!/usr/bin/env python3
"""
test_exe_sjis_strings.py -- pin the shipped EXE SJIS/NPC-name string patches.

CLAUDE.md claims "EXE SJIS Strings -- COMPLETE (8 patches)".  Until now NOTHING
byte-asserted the built EXE actually carries them (July-2 audit gap #2 of the
top-5).  This module pins build/patch_exe.py's three string-table patch blocks
against build/SLPM_653.78_patched:

  * Patch 1 (Table 2G): 6 save-slot names -- the 'BUSIN 0' family at file
    0x3FC720/0x3FC750/0x3FC770/0x3FC790/0x3F9370/0x3F9678, ASCII + NUL-fill.
  * Patch 2 (Table 2L): the 2 player-visible SJIS strings at 0x3F8240/0x3F8260
    ("Continue loading!\\n" / "No one can equip it.\\n").
  * Patch 3 (Table 2F): the NPC names at 0x3C93B0 -- Emilia/Lute as LE-u16
    glyph ids (ord(c)-0x20), 0xFFFF-padded to 8 slots each.

Plus the two guards that make the pin trustworthy:
  * the PRISTINE extract (extracted/SLPM_653.78) still carries the documented
    SJIS/glyph originals at every site (mirrored constants have not drifted),
  * the bytes AROUND each patched window are byte-identical to pristine (the
    patcher wrote exactly its declared windows, nothing more).

Constants are MIRRORED from build/patch_exe.py (Patch 1/2/3 blocks) -- if the
patcher's tables change, update here in lockstep (the pristine-guard test will
catch silent drift on the originals).
TIER-2: SKIPs when the built/pristine EXE is absent.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit

PRISTINE_EXE = os.path.join(ROOT, "extracted", "SLPM_653.78")
PATCHED_EXE = os.path.join(ROOT, "build", "SLPM_653.78_patched")
# v175 FIX B: ZERO ELF-structure change -- no added segment, no file growth.  The
# built EXE is byte-length IDENTICAL to the pristine EXE (4,185,776); the font-metric
# tables live in the freed tail of the shrunk libc strncpy (@VA 0x121568), fully inside
# the existing .text.  Every string-patch window is unaffected.
PRISTINE_SIZE = 4_185_776
OUTPUT_SIZE = 4_185_776
EXPECTED_SIZES = {"pristine EXE": PRISTINE_SIZE,
                  "built EXE (run build/patch_exe.py)": OUTPUT_SIZE}

# ── Patch 1: save-slot names (offset, window_size, pristine_sjis_hex, ascii) ──
SAVE_SLOT_PATCHES = [
    (0x3FC720, 16, "8261827482728268826d824f",                     "BUSIN 0"),
    (0x3FC750, 32, "8261827482728268826d824f8366815b835e8250",     "BUSIN 0 Data 1"),
    (0x3FC770, 32, "8261827482728268826d824f8366815b835e8251",     "BUSIN 0 Data 2"),
    (0x3FC790, 32, "8261827482728268826d824f8366815b835e8252",     "BUSIN 0 Data 3"),
    (0x3F9370, 24, "8261827482728268826d824f928692668366815b835e", "BUSIN 0 Suspend"),
    (0x3F9678, 12, "8261827482728268826d824f",                     "BUSIN 0"),
]

# ── Patch 2: player-visible strings ──
PLAYER_STRING_PATCHES = [
    (0x3F8240, 32, "8352839383658342836a8385815b838d815b836881490a",
     "Continue loading!\n"),
    (0x3F8260, 32, "8ee682e8957482af82e9906c82aa82a282c882a282e681420a",
     "No one can equip it.\n"),
]

# ── Patch 3: NPC names (LE u16 glyph ids, glyph = ord(c) - 0x20) ──
NPC_OFFSET = 0x3C93B0
NPC_WINDOW = 32  # name1 (16 bytes) + name2 (16 bytes)
NPC_PRISTINE_NAME1 = [196, 224, 93, 232, 193, 0xFFFF, 0xFFFF, 0xFFFF]
NPC_PRISTINE_NAME2_PREFIX = [232, 265, 93, 212, 0xFFFF]
NPC_NEW_NAME1 = ("Emilia", 8)  # text, total u16 slots (0xFFFF-padded)
NPC_NEW_NAME2 = ("Lute", 8)

MARGIN = 16  # bytes checked pristine on each side of every patched window

# All byte windows the three patch blocks are allowed to touch.
PATCH_WINDOWS = (
    [(off, off + avail) for off, avail, _h, _t in SAVE_SLOT_PATCHES]
    + [(off, off + avail) for off, avail, _h, _t in PLAYER_STRING_PATCHES]
    + [(NPC_OFFSET, NPC_OFFSET + NPC_WINDOW)]
)


_CACHE = {}


def _exe(path, tag):
    if tag not in _CACHE:
        if not os.path.isfile(path):
            raise Skip("%s missing (%s)" % (os.path.relpath(path, ROOT), tag))
        data = open(path, "rb").read()
        want = EXPECTED_SIZES[tag]
        assert len(data) == want, (
            "%s is %d bytes, expected %d -- wrong EXE?"
            % (os.path.relpath(path, ROOT), len(data), want)
        )
        _CACHE[tag] = data
    return _CACHE[tag]


def _pristine():
    return _exe(PRISTINE_EXE, "pristine EXE")


def _patched():
    return _exe(PATCHED_EXE, "built EXE (run build/patch_exe.py)")


def _encode_glyph_ids(text, total_slots):
    """Mirror patch_exe.encode_glyph_ids + 0xFFFF slot padding."""
    out = b"".join(struct.pack("<H", ord(c) - 0x20) for c in text)
    out += b"\xff\xff" * (total_slots - len(text))
    return out


def _ascii_window(text, avail):
    enc = text.encode("ascii")
    assert len(enc) + 1 <= avail, "mirrored string %r does not fit %d" % (text, avail)
    return enc + b"\x00" * (avail - len(enc))


def _in_any_window(i):
    return any(s <= i < e for s, e in PATCH_WINDOWS)


# ===========================================================================
# Guard: the pristine extract still carries the documented originals.
# ===========================================================================
def test_pristine_originals_still_match_mirror():
    """If this fails, the mirrored constants drifted from build/patch_exe.py
    (or extracted/SLPM_653.78 is not the pristine SLPM-65378 EXE)."""
    pr = _pristine()
    for off, _avail, sjis_hex, text in SAVE_SLOT_PATCHES + PLAYER_STRING_PATCHES:
        want = bytes.fromhex(sjis_hex)
        got = pr[off:off + len(want)]
        assert got == want, (
            "pristine EXE @0x%06X: SJIS original %s != documented %s "
            "(patch target for %r moved -- update the mirror from patch_exe.py)"
            % (off, got.hex(), sjis_hex, text)
        )
    name1 = list(struct.unpack_from("<8H", pr, NPC_OFFSET))
    assert name1 == NPC_PRISTINE_NAME1, (
        "pristine NPC name1 glyphs @0x%06X = %s, expected %s"
        % (NPC_OFFSET, name1, NPC_PRISTINE_NAME1)
    )
    name2 = list(struct.unpack_from("<5H", pr, NPC_OFFSET + 16))
    assert name2 == NPC_PRISTINE_NAME2_PREFIX, (
        "pristine NPC name2 glyph prefix @0x%06X = %s, expected %s"
        % (NPC_OFFSET + 16, name2, NPC_PRISTINE_NAME2_PREFIX)
    )


# ===========================================================================
# Patch 1: save-slot names shipped
# ===========================================================================
def test_save_slot_names_patched():
    bd = _patched()
    for off, avail, _sjis, text in SAVE_SLOT_PATCHES:
        want = _ascii_window(text, avail)
        got = bd[off:off + avail]
        assert got == want, (
            "built EXE @0x%06X: save-slot window = %s, expected %r + NUL fill "
            "-- Patch 1 (Table 2G) not shipping" % (off, got.hex(), text)
        )


# ===========================================================================
# Patch 2: player-visible strings shipped
# ===========================================================================
def test_player_visible_strings_patched():
    bd = _patched()
    for off, avail, _sjis, text in PLAYER_STRING_PATCHES:
        want = _ascii_window(text, avail)
        got = bd[off:off + avail]
        assert got == want, (
            "built EXE @0x%06X: string window = %s, expected %r + NUL fill "
            "-- Patch 2 (Table 2L) not shipping" % (off, got.hex(), text)
        )


# ===========================================================================
# Patch 3: NPC names shipped
# ===========================================================================
def test_npc_names_patched():
    bd = _patched()
    text1, slots1 = NPC_NEW_NAME1
    want1 = _encode_glyph_ids(text1, slots1)
    got1 = bd[NPC_OFFSET:NPC_OFFSET + slots1 * 2]
    assert got1 == want1, (
        "built EXE @0x%06X: NPC name1 = %s, expected %r as LE glyph ids + FFFF "
        "pad -- Patch 3 (Emilia) not shipping" % (NPC_OFFSET, got1.hex(), text1)
    )
    text2, slots2 = NPC_NEW_NAME2
    want2 = _encode_glyph_ids(text2, slots2)
    got2 = bd[NPC_OFFSET + 16:NPC_OFFSET + 16 + slots2 * 2]
    assert got2 == want2, (
        "built EXE @0x%06X: NPC name2 = %s, expected %r as LE glyph ids + FFFF "
        "pad -- Patch 3 (Lute) not shipping" % (NPC_OFFSET + 16, got2.hex(), text2)
    )


# ===========================================================================
# Containment: the bytes AROUND each patched window are pristine.
# ===========================================================================
def test_bytes_around_each_site_pristine():
    """Guards the 'COMPLETE' claim: the string patches touch EXACTLY their
    declared windows.  MARGIN bytes on each side of every window must be
    byte-identical to pristine (margin bytes falling inside a NEIGHBOURING
    declared window are exempt -- e.g. 0x3F8240+32 == 0x3F8260)."""
    pr, bd = _pristine(), _patched()
    bad = []
    for start, end in PATCH_WINDOWS:
        for i in list(range(start - MARGIN, start)) + list(range(end, end + MARGIN)):
            if i < 0 or i >= len(pr) or _in_any_window(i):
                continue
            if pr[i] != bd[i]:
                bad.append((i, start, end))
    assert not bad, (
        "%d byte(s) around string-patch windows differ from pristine (first: "
        "0x%06X beside window 0x%06X..0x%06X) -- a string patch overran its slot"
        % (len(bad), bad[0][0], bad[0][1], bad[0][2])
    )


TESTS = [
    test_pristine_originals_still_match_mirror,
    test_save_slot_names_patched,
    test_player_visible_strings_patched,
    test_npc_names_patched,
    test_bytes_around_each_site_pristine,
]

if __name__ == "__main__":
    main_exit(TESTS, "test_exe_sjis_strings")
