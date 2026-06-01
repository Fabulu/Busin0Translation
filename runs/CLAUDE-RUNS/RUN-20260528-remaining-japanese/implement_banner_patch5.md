# Patch 5: Banner byte-50 glyph IDs

## What

Each banner menu record for the chargen banner has a **third** glyph reference at byte 50 (offset +50 from record start). Patch 4 handled the glyph pairs at bytes 24-47; Patch 5 fixes the remaining single glyph at byte 50 so the full banner renders correctly.

## Offsets patched

| Absolute offset | Record start | Byte | Old glyph | New glyph | Char |
|-----------------|-------------|------|-----------|-----------|------|
| 0x3C3422        | 0x3C33F0    | 50   | 498       | 46        | n    |
| 0x3C345A        | 0x3C3428    | 50   | 499       | 37        | e    |
| 0x3C329A        | 0x3C3268    | 50   | 491       | 55        | w    |
| 0x3C32D2        | 0x3C32A0    | 50   | 492       | 0         | space|

## Verification

All 4 offsets verified against unpatched EXE -- original values match expected glyph IDs (498, 499, 491, 492). Full patch_exe.py run completed with 18/18 patches OK.

## File modified

`build/patch_exe.py` -- Patch 5 added after Patch 4 (lines ~217-241).
