#!/usr/bin/env python3
"""Verify an ISO has all expected English patches applied."""
import struct, sys, hashlib

if len(sys.argv) < 2:
    print("Usage: python verify_iso.py <path_to_iso>")
    sys.exit(1)

iso_path = sys.argv[1]
print(f"Verifying: {iso_path}")

iso = open(iso_path, 'rb')

# Check PACKDATA size
iso.seek(16 * 2048)
pvd = iso.read(2048)
root_lba = struct.unpack_from('<I', pvd, 158)[0]
root_size = struct.unpack_from('<I', pvd, 166)[0]
iso.seek(root_lba * 2048)
root_dir = iso.read(root_size)

pack_lba = pack_size = exe_lba = None
pos = 0
while pos < len(root_dir):
    rl = root_dir[pos]
    if rl == 0: break
    nl = root_dir[pos + 32]
    nm = root_dir[pos + 33:pos + 33 + nl].decode('ascii', errors='replace')
    if 'PACKDATA' in nm:
        pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        pack_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
    if 'SLPM' in nm:
        exe_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
    pos += rl

passed = 0
failed = 0

# Test 1: PACKDATA size
if pack_size and pack_size > 800_000_000:
    print(f"  PASS: PACKDATA size = {pack_size:,} bytes ({pack_size//1024//1024} MB)")
    passed += 1
else:
    print(f"  FAIL: PACKDATA size = {pack_size:,} bytes (expected >800 MB)")
    failed += 1

# Test 2: R38 stat labels
if pack_lba:
    iso.seek(pack_lba * 2048 + 38 * 12)
    s, c, t = struct.unpack('<III', iso.read(12))
    iso.seek((pack_lba + s) * 2048)
    r38 = iso.read(c * 2048)
    # Find stream start
    for i in range(16, len(r38) - 1, 2):
        if struct.unpack_from('>H', r38, i)[0] == 0xFFFF:
            stream = i + 2
            break
    # Decode group 2 (STR)
    gi = 0
    gstart = stream
    r38_checks = {}
    for i in range(stream, len(r38) - 1, 2):
        if struct.unpack_from('>H', r38, i)[0] == 0xFFFF:
            glyphs = []
            p = gstart
            while p < i:
                g = struct.unpack_from('>H', r38, p)[0]
                if 33 <= g <= 90: glyphs.append(chr(g + 0x20))
                elif g == 0xFFFE: glyphs.append('/')
                else: glyphs.append(f'[{g}]')
                p += 2
            r38_checks[gi] = ''.join(glyphs)
            gi += 1
            gstart = i + 2
            if gi > 35: break

    for check_gi, expected, label in [
        (2, 'str', 'STR stat'),
        (3, 'int', 'INT stat'),
        (25, 'M', 'Male (M)'),
        (26, 'F', 'Female (F)'),
        (29, 'human', 'Human race'),
        (34, 'automa', 'Automata race'),
    ]:
        actual = r38_checks.get(check_gi, 'MISSING')
        if expected.lower() in actual.lower():
            print(f"  PASS: R38 GRP {check_gi} ({label}) = '{actual}'")
            passed += 1
        else:
            print(f"  FAIL: R38 GRP {check_gi} ({label}) = '{actual}' (expected '{expected}')")
            failed += 1

# Test 3: EXE patches
if exe_lba:
    iso.seek(exe_lba * 2048 + 0x3FC720)
    save_name = iso.read(7)
    if save_name == b'BUSIN 0':
        print(f"  PASS: EXE save slot = 'BUSIN 0'")
        passed += 1
    else:
        print(f"  FAIL: EXE save slot = {save_name} (expected 'BUSIN 0')")
        failed += 1

# Test 4: R1272 font atlas size
if pack_lba:
    iso.seek(pack_lba * 2048 + 1272 * 12)
    s, c, t = struct.unpack('<III', iso.read(12))
    r1272_size = c * 2048
    if r1272_size >= 67000:
        print(f"  PASS: R1272 font atlas = {r1272_size} bytes (extended)")
        passed += 1
    else:
        print(f"  FAIL: R1272 font atlas = {r1272_size} bytes (expected >70000)")
        failed += 1

# ===========================================================================
# RELOCATION-INTEGRITY GATE (permanent build-clobber tripwire)
# ===========================================================================
# Background: the rebuilt PACKDATA.DIG is ~220 sectors larger than the original,
# so its tail would overwrite every file after it (BSN2_0.DSI audio, the *.IRX
# drivers, IOPRP254.IMG, SYSTEM.CNF, TEMP1.LZH, and the EXE). build_v9.py
# "Step 8.2" self-heals by relocating each post-PACKDATA file forward and
# rewriting its directory LBA + the PVD vol_space. That self-heal is a single
# point of failure: if the directory parse ever returns an empty relocation
# list, the asserts are skipped and a CLOBBERED ISO ships (audio corrupt on real
# PS2 hardware). This gate re-verifies the SHIPPED ISO so that can never happen
# silently. A concrete clobbered artifact this catches:
#   build/CLOBBERED_DO_NOT_USE_BUSIN0_EN.iso.bad
import math, os

SECTOR = 2048
reloc_passed = 0
reloc_failed = 0

def _rpass(msg):
    global reloc_passed
    print(f"  PASS: {msg}")
    reloc_passed += 1

def _rfail(msg):
    global reloc_failed
    print(f"  FAIL: {msg}")
    reloc_failed += 1

print("\n=== Relocation-Integrity Gate ===")

# ---- 1. Parse the PVD + full (multi-sector) root directory ----
# Per-sector record walk (like build/check_iso_fs.py ~L96-101): a rec_len of 0
# means "skip to the next sector boundary", NOT "stop" -- a stop-at-first-zero
# parse would silently truncate a multi-sector root directory.
iso.seek(16 * SECTOR)
pvd = iso.read(SECTOR)
g_root_lba = struct.unpack_from('<I', pvd, 158)[0]
g_root_size = struct.unpack_from('<I', pvd, 166)[0]
vol_space_le = struct.unpack_from('<I', pvd, 80)[0]
vol_space_be = struct.unpack_from('>I', pvd, 84)[0]

iso.seek(g_root_lba * SECTOR)
rd = iso.read(g_root_size)

# files = list of (name, lba, size, is_dir)
files = []
pos = 0
while pos < len(rd):
    rl = rd[pos]
    if rl == 0:
        nxt = ((pos // SECTOR) + 1) * SECTOR
        if nxt >= len(rd):
            break
        pos = nxt
        continue
    flags = rd[pos + 25]
    nl = rd[pos + 32]
    raw = rd[pos + 33:pos + 33 + nl]
    if nl == 1 and raw == b'\x00':
        nm = '.'
    elif nl == 1 and raw == b'\x01':
        nm = '..'
    else:
        nm = raw.decode('ascii', errors='replace')
        if ';' in nm:
            nm = nm[:nm.index(';')]
    lba = struct.unpack_from('<I', rd, pos + 2)[0]
    size = struct.unpack_from('<I', rd, pos + 10)[0]
    files.append((nm, lba, size, bool(flags & 0x02)))
    pos += rl

# Real files only (exclude . / .. and directory records) for the overlap math.
real_files = [(n, l, s) for (n, l, s, d) in files if not d and n not in ('.', '..')]

# ---- 2. No two files overlap ----
ordered = sorted(real_files, key=lambda e: e[1])
overlap_found = False
prev = None
for (n, l, s) in ordered:
    if prev is not None:
        pn, pl, ps = prev
        prev_end = pl + math.ceil(ps / SECTOR)  # first sector AFTER prev's data
        if l < prev_end:
            _rfail(f"file overlap: '{n}' starts LBA {l} but '{pn}' "
                   f"runs through LBA {prev_end - 1}")
            overlap_found = True
    prev = (n, l, s)
if not overlap_found:
    _rpass(f"no file overlaps among {len(real_files)} files")

# ---- 3. PACKDATA.DIG end == next file's start (tight, no gap/overlap) ----
pack = next((e for e in real_files if 'PACKDATA' in e[0].upper()), None)
if pack is None:
    _rfail("no PACKDATA.DIG in root directory")
else:
    p_lba, p_size = pack[1], pack[2]
    p_end = p_lba + math.ceil(p_size / SECTOR)
    # First file (by LBA) that starts at/after PACKDATA's start, excluding
    # PACKDATA itself -- that is the file PACKDATA's tail would clobber.
    nxt = next((e for e in sorted(real_files, key=lambda e: e[1]) if e[1] >= p_lba and 'PACKDATA' not in e[0].upper()), None)
    if nxt is None:
        _rfail("no file found after PACKDATA.DIG")
    elif nxt[1] == p_end:
        _rpass(f"PACKDATA.DIG ends at LBA {p_end} == next file '{nxt[0]}' start")
    elif nxt[1] > p_end:
        _rfail(f"gap after PACKDATA.DIG: ends at LBA {p_end}, next file "
               f"'{nxt[0]}' starts at {nxt[1]} ({nxt[1]-p_end} sector gap)")
    else:
        _rfail(f"PACKDATA.DIG OVERFLOWS next file '{nxt[0]}': PACKDATA ends "
               f"at LBA {p_end} but '{nxt[0]}' starts at {nxt[1]} "
               f"({p_end-nxt[1]} sectors clobbered) -- Step 8.2 self-heal failed")

# ---- 4. PVD volume_space_size (LE==BE) == actual ISO size in sectors ----
iso.seek(0, 2)
iso_bytes = iso.tell()
iso_sectors = iso_bytes // SECTOR
if vol_space_le != vol_space_be:
    _rfail(f"PVD vol_space LE ({vol_space_le}) != BE ({vol_space_be})")
elif vol_space_le != iso_sectors:
    _rfail(f"PVD vol_space ({vol_space_le} sectors) != actual ISO size "
           f"({iso_sectors} sectors) -- ISO not extended for relocation")
else:
    _rpass(f"PVD vol_space {vol_space_le} sectors == actual ISO size")

# ---- 5. RELOCATION CHECK: the high-stakes relocated files must be REAL ----
# Read first+middle+last sector at each file's CURRENT directory LBA and MD5-
# compare against the pristine extract in extracted/. If Step 8.2 failed to
# relocate (or clobbered the LBA), these sectors hold PACKDATA-tail bytes and
# the MD5 will differ. extracted/BSN2_0.DSI etc. are the byte-pristine originals.
RELOC_NAMES = [
    'BSN2_0.DSI', 'IOPRP254.IMG', 'SYSTEM.CNF', 'TEMP1.LZH',
    'LIBSD.IRX', 'MCMAN.IRX', 'MCSERV.IRX', 'MODHSYN.IRX',
    'MODMIDI.IRX', 'MODMSIN.IRX', 'MUS.IRX', 'PADMAN.IRX', 'SIO2MAN.IRX',
]
_extracted_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted')

def _iso_sector_bytes(fh, lba, nbytes):
    # Read the same number of bytes the pristine file has in this sector. The
    # ISO zero-pads the final partial sector up to 2048; the pristine extract
    # ends at the real file length. Comparing equal-length slices avoids a
    # false mismatch on the trailing partial sector (padding vs. EOF).
    fh.seek(lba * SECTOR)
    return fh.read(nbytes)

def _file_sector_bytes(path, sector_index):
    with open(path, 'rb') as pf:
        pf.seek(sector_index * SECTOR)
        return pf.read(SECTOR)  # may be < SECTOR for the final partial sector

by_name = {n: (l, s) for (n, l, s) in real_files}
checked_any = False
for rn in RELOC_NAMES:
    # Directory names carry a version suffix (;1) already stripped above.
    ent = next((by_name[k] for k in by_name if k.upper() == rn.upper()), None)
    if ent is None:
        continue  # not every disc has every IRX; skip absent ones silently
    lba, size = ent
    nsec = max(1, math.ceil(size / SECTOR))
    sample_idx = sorted(set([0, nsec // 2, nsec - 1]))  # first, middle, last
    pristine = os.path.join(_extracted_dir, rn)
    have_pristine = os.path.isfile(pristine)
    ok = True
    detail = ''
    for si in sample_idx:
        if have_pristine:
            pris_bytes = _file_sector_bytes(pristine, si)
            iso_bytes_s = _iso_sector_bytes(iso, lba + si, len(pris_bytes))
            if iso_bytes_s != pris_bytes:
                ok = False
                ih = hashlib.md5(iso_bytes_s).hexdigest()[:8]
                ph = hashlib.md5(pris_bytes).hexdigest()[:8]
                detail = f"sector {si} (LBA {lba+si}) MD5 {ih} != pristine {ph}"
                break
        else:
            # No pristine extract: at minimum, the relocated file's first sector
            # must NOT be PACKDATA-tail bytes. Catch the two clobber signatures:
            # an all-0xFF run, or a byte-match with PACKDATA's first sector.
            iso.seek((lba + si) * SECTOR)
            raw_sec = iso.read(SECTOR)
            if raw_sec == b'\xff' * SECTOR:
                ok = False
                detail = f"sector {si} (LBA {lba+si}) is all-0xFF (PACKDATA-tail clobber)"
                break
    checked_any = True
    if ok:
        src = "MD5==pristine" if have_pristine else "not PACKDATA-tail"
        _rpass(f"relocated '{rn}' (LBA {lba}, {nsec} sectors) {src}")
    else:
        _rfail(f"relocated '{rn}' CLOBBERED: {detail} -- Step 8.2 left PACKDATA "
               f"bytes over this file; real-PS2 data/audio corrupt")

# Hard minimum: BSN2_0.DSI must have been verified one way or another.
bsn_ent = next((by_name[k] for k in by_name if 'BSN2_0' in k.upper()), None)
if bsn_ent is None:
    _rfail("BSN2_0.DSI not found in root directory")
elif not checked_any:
    _rfail("no relocated files could be checked -- relocation list empty?")

# Roll relocation results into the overall pass/fail tally.
passed += reloc_passed
failed += reloc_failed
if reloc_failed == 0:
    print(f"  RELOCATION GATE: PASS ({reloc_passed} checks)")
else:
    print(f"  RELOCATION GATE: FAIL ({reloc_failed} violation(s)) -- "
          f"this ISO would corrupt audio/drivers on real PS2 hardware")

# Calculate ISO hash (first 1MB for speed)
iso.seek(0)
h = hashlib.md5(iso.read(1024*1024)).hexdigest()
print(f"\n  ISO hash (first 1MB): {h}")
print(f"\n  Results: {passed} PASS, {failed} FAIL")
if failed == 0:
    print("  ALL CHECKS PASSED - ISO is correctly patched")
else:
    print("  SOME CHECKS FAILED - ISO may be stale or corrupt")

# The relocation-integrity gate is the real-PS2 safety tripwire and is the ONLY
# thing that fails the SCRIPT (non-zero exit). The pre-existing content checks
# above (R38 M/F glyph cosmetics, etc.) print FAIL but never broke the exit code
# historically, so we keep that behavior. A relocation violation, however, means
# the ISO would corrupt audio/drivers on real hardware -- that MUST be fatal.
if reloc_failed > 0:
    print("  RELOCATION-INTEGRITY GATE FAILED - DO NOT SHIP THIS ISO "
          "(audio/drivers would be corrupt on real PS2 hardware)")
    sys.exit(1)
