#!/usr/bin/env python3
"""
p2s_extract.py -- read the useful members out of a PCSX2 save-state (.p2s).

A .p2s is a plain ZIP archive.  The members this project cares about:

  * Screenshot.png  -- 640x480 RGBA PNG, ZIP-STORED (compress method 0).
                       The LAST rendered frame at capture time.  Ground truth
                       for the framebuffer.  A black/blank frame is ~2.9 KB; a
                       real rendered frame is 200-460 KB.
  * eeMemory.bin    -- the full 32 MB EE RAM, ZIP method 93 == a single raw
                       zstd frame (magic 28 b5 2f fd).  IMPORTANT: this image
                       is VA-DIRECT -- ee[VA] is the byte living at that virtual
                       address (RAM == VA).  It is NOT the EXE FILE layout; the
                       EXE on disc uses fo(va) = va - 0x100000 + 0x80.
  * GS.bin          -- a 509-byte header followed by 4 MB of GS VRAM.

Every member is decompressed by hand (via the local-file-header offset) so a
STORED member and a zstd (method-93) member are both handled -- Python's
zipfile does not know method 93.

Public API (all return bytes / lists; raise KeyError if a member is absent):
    members(path)      -> [member names]
    screenshot(path)   -> PNG bytes (the Screenshot.png member)
    ee_ram(path)       -> 32 MB EE RAM (VA-direct)
    vram(path)         -> 4 MB GS VRAM (GS.bin after its 509-byte header)
    raw_member(path,n) -> bytes of member n (STORED or zstd)

CLI:
    python tools/p2s_extract.py <file.p2s>
    python tools/p2s_extract.py <file.p2s> --screenshot out.png --ee out.bin
"""

import argparse
import os
import struct
import sys
import zipfile

# Windows console is cp1252 -- keep any stray glyph output alive.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"
GS_HEADER_LEN = 509  # GS.bin = 509-byte header + VRAM


# ---------------------------------------------------------------------------
# low-level member reader (handles STORED + zstd method-93)
# ---------------------------------------------------------------------------
def _read_member(z, info):
    """Return the decompressed bytes of ZipInfo `info` from open ZipFile `z`.

    Reads the local file header directly to skip the (variable) filename +
    extra fields, then decompresses.  method 0 = STORED (raw), anything else
    is treated as a raw zstd frame (PCSX2 uses method 93)."""
    zf = z.fp
    zf.seek(info.header_offset)
    lfh = zf.read(30)
    if lfh[:4] != b"PK\x03\x04":
        raise ValueError("bad local file header for %r" % info.filename)
    name_len = struct.unpack_from("<H", lfh, 26)[0]
    extra_len = struct.unpack_from("<H", lfh, 28)[0]
    zf.seek(info.header_offset + 30 + name_len + extra_len)
    raw = zf.read(info.compress_size)
    if info.compress_type == zipfile.ZIP_STORED:
        return raw
    # method 93 (or any non-STORED PCSX2 member) == a single raw zstd frame.
    if raw[:4] != ZSTD_MAGIC:
        # Fall back to zipfile's own decoders for a recognised method.
        try:
            return z.read(info.filename)
        except Exception as e:  # pragma: no cover
            raise ValueError(
                "member %r: compress method %d, not STORED and not a zstd "
                "frame (%s)" % (info.filename, info.compress_type, e)
            )
    import zstandard as zstd  # local import so callers without a member still work

    return zstd.ZstdDecompressor().decompress(raw, max_output_size=info.file_size)


def _find(z, basename):
    """Case-insensitive EXACT basename match among the archive members."""
    want = basename.lower()
    for info in z.infolist():
        if os.path.basename(info.filename).lower() == want:
            return info
    raise KeyError(
        "%r not found in save-state (members: %s)"
        % (basename, ", ".join(i.filename for i in z.infolist()))
    )


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------
def members(path):
    """List every member name in the .p2s archive."""
    with zipfile.ZipFile(path) as z:
        return z.namelist()


def raw_member(path, basename):
    """Decompressed bytes of the named member (STORED or zstd)."""
    with zipfile.ZipFile(path) as z:
        return _read_member(z, _find(z, basename))


def screenshot(path):
    """Screenshot.png bytes (the last rendered frame; STORED PNG)."""
    return raw_member(path, "Screenshot.png")


def ee_ram(path):
    """The full 32 MB EE RAM image, VA-direct (ee[VA] == byte at VA)."""
    return raw_member(path, "eeMemory.bin")


def vram(path):
    """The 4 MB GS VRAM (GS.bin with its 509-byte header stripped)."""
    gs = raw_member(path, "GS.bin")
    if len(gs) < GS_HEADER_LEN:
        raise ValueError("GS.bin too short (%d bytes) for a 509-byte header" % len(gs))
    return gs[GS_HEADER_LEN:]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _main(argv=None):
    ap = argparse.ArgumentParser(description="Extract members from a PCSX2 .p2s save-state.")
    ap.add_argument("p2s", help="path to a .p2s save-state (a ZIP archive)")
    ap.add_argument("--screenshot", metavar="OUT.png", help="write Screenshot.png here")
    ap.add_argument("--ee", metavar="OUT.bin", help="write the 32MB EE RAM here (VA-direct)")
    ap.add_argument("--vram", metavar="OUT.bin", help="write the 4MB GS VRAM here")
    ap.add_argument("--list", action="store_true", help="list members and exit")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.p2s):
        print("ERROR: no such file: %s" % args.p2s)
        return 2

    names = members(args.p2s)
    print("%s  (%d members)" % (args.p2s, len(names)))
    if args.list or not (args.screenshot or args.ee or args.vram):
        with zipfile.ZipFile(args.p2s) as z:
            for info in z.infolist():
                meth = "STORED" if info.compress_type == 0 else "m%d" % info.compress_type
                print("  %-34s %-8s %d bytes" % (info.filename, meth, info.file_size))
        # A quick free health read: the Screenshot.png byte size + mode sentinel.
        try:
            ss = screenshot(args.p2s)
            print("Screenshot.png: %d bytes (%s)"
                  % (len(ss), "LOOKS BLACK/blank" if len(ss) < 10000 else "rendered frame"))
        except KeyError:
            pass

    if args.screenshot:
        data = screenshot(args.p2s)
        open(args.screenshot, "wb").write(data)
        print("wrote %s (%d bytes)" % (args.screenshot, len(data)))
    if args.ee:
        data = ee_ram(args.p2s)
        open(args.ee, "wb").write(data)
        print("wrote %s (%d bytes, VA-direct)" % (args.ee, len(data)))
    if args.vram:
        data = vram(args.p2s)
        open(args.vram, "wb").write(data)
        print("wrote %s (%d bytes)" % (args.vram, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
