"""
patch_prequel_us_save.py -- retarget the predecessor-save bonus probe to the US region

Busin 0 (SLPM-65378) grants new-game chargen bonuses (+10 protagonist bonus points, better
starting gear, pre-made companions renamed after the prequel's characters) if the memory
card holds a *Wizardry: Tale of the Forsaken Land* (BUSIN 1) save. Stock SLPM-65378 checks
the JAPANESE directory `BISLPM-62098BUSINWZ`. Almost nobody playing an English patch owns
the JP prequel; they own the US release (SLUS-20259), whose card directory is
`BASLUS-20259WIZTFL`. This patch retargets the single probe string to the US directory so
the bonus fires from a US prequel save.

This is an in-place swap of ONE string -- no code cave, no arena/libgraph risk, works on
real PS2 hardware. Trade-off: it swaps JP -> US (drops JP detection). The JP+US dual-region
retry is designed but held (needs reclaimed code space) -- see tools/patch_prequel_dualregion.py.

MECHANISM: the probe (handler VA 0x48EE20) builds an mc path from the string hardcoded at
VA 0x48EE78 -> VA 0x4F95E0, then checks the card for that directory and sets found-bit
0x20000 in *(gp-25220), which chargen reads. `BISLPM-62098BUSINWZ` (19 bytes) is the full
concatenated directory name; `BASLUS-20259WIZTFL` (18 bytes) is shorter, so it overwrites
in place (the trailing NUL is preserved). Both directory names were verified against the
real US disc EXE (SLUS_202.59) and a real MaxDrive save header.

Idempotent; asserts the stock JP string is present before swapping and ABORTS otherwise.

Usage:  python tools/patch_prequel_us_save.py <exe_in> [<exe_out>]  (in-place if omitted)
        or import and call apply(path) from the build.
"""

import os
import sys

STR_VA = 0x4F95E0                       # probe directory string (only xref: 0x48EE78)
STR_FO = STR_VA - 0x100000 + 0x80       # file 0x3F9660
JP = b"BISLPM-62098BUSINWZ"             # 19 bytes (stock)
US = b"BASLUS-20259WIZTFL"              # 18 bytes (US: SLUS-20259 Tale of the Forsaken Land)
NEW = US + b"\x00"                      # 19 bytes: overwrite JP(19) incl. writing a NUL


def apply(exe_in, exe_out=None):
    exe_out = exe_out or exe_in
    with open(exe_in, "rb") as f:
        data = bytearray(f.read())

    cur = bytes(data[STR_FO:STR_FO + 19])
    if cur[:18] == US:
        print("  patch_prequel_us_save: already applied - no-op")
        if exe_out != exe_in:
            with open(exe_out, "wb") as f:
                f.write(data)
        return False
    if cur != JP:
        raise SystemExit(
            "ABORT patch_prequel_us_save: string @0x%X is %r, expected the stock JP "
            "directory %r (EXE not the expected build)" % (STR_VA, cur, JP))

    data[STR_FO:STR_FO + len(NEW)] = NEW

    assert bytes(data[STR_FO:STR_FO + 18]) == US
    assert data[STR_FO + 18] == 0, "US string must be NUL-terminated"
    with open(exe_out, "wb") as f:
        f.write(data)
    print("  patch_prequel_us_save: OK - probe retargeted to US dir BASLUS-20259WIZTFL "
          "(@0x%X)" % STR_VA)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    apply(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
