# Shift -1 Verification Report (R37/R48/R49)

## Summary
The -1 shift on R37/R48/R49 message indices is CORRECT and did NOT break anything.

## What the shift fixed
All 232 entries in `chunk_r37_r48_r49_translated.json` and `chunk_r37_extra.json` had message indices that were +1 too high. Subtracting 1 from every `"message"` field aligned them with the actual FFFF-group numbering in the binary.

## Verification Details

### R37 (chargen prompts, keyboards, preset names)
- Binary has 127 FFFF groups (indices 0-126)
- After shift, translations cover indices 1-125 (125 entries) -- all within range
- Critical alignments confirmed:
  - msg 8 = "Bonus Point" (was incorrectly at msg 9)
  - msg 9 = "Yes" (was incorrectly at msg 10)
  - msg 10 = "No" (was incorrectly at msg 11)
  - msg 1 = "Enter your name." -- correct
  - msg 7 = "Is this OK?" -- correct

### R48 (shop/building names)
- 107 entries, indices 0-106 -- matches decoded text exactly
- msg 0 = "None" (matches JP "nashi"), msg 1 = "Illegal Dump Site" (matches JP) -- correct

### R49 (dungeon event messages)
- 111 entries, indices 0-110 -- matches decoded text
- msg 0 = "Nothing unusual here" (matches JP), msg 1 = "It won't open from this side" -- correct

## Conflict Check: chunk_r37_extra.json vs chunk_01_translated.json

**No conflict.** Here is why:

- `chunk_01_translated.json` has 15 R37 entries (msgs 1-18, some gaps)
- These entries used CORRECT indices from the start (they were never off-by-one)
- After the -1 shift, `chunk_r37_r48_r49_translated.json` and `chunk_r37_extra.json` now use the SAME correct numbering
- The build pipeline loads chunk_01 FIRST, then loads main/extra as OVERRIDES
- Every single chunk_01 R37 entry is overridden by main or extra -- zero chunk_01 R37 entries survive dedup
- Therefore the indices in chunk_01 are irrelevant for R37

Overlap summary:
- 12 chunk_01 R37 entries overridden by `chunk_r37_r48_r49_translated.json`
- 3 chunk_01 R37 entries overridden by `chunk_r37_extra.json`
- 0 chunk_01 R37 entries survive (all overridden)

## Screenshot Check (v32, 32-1_Screenshot.png)

The screenshot shows the name entry screen:
- "Enter your name." prompt displays correctly (R37 msg 1)
- Keyboard layout renders properly (ABCDE... grid)
- "M name" / "F name" buttons visible at bottom
- Sidebar labels (Kana, etc.) are still Japanese -- these come from R1188 texture, not R37 msg data
- Header "New Registration" still Japanese -- likely hardcoded in EXE or a different resource

## Conclusion

The -1 shift is safe. All 232 entries now target the correct FFFF groups. No conflicts with chunk_01. A rebuild will produce correct results.
