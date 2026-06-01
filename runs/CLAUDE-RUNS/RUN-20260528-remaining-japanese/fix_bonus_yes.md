# Fix: R37/R48/R49 Off-by-One Message Index Bug

## Problem
The stat allocation confirmation screen showed "Bonus Points" as the accept button and "Yes" as the cancel/back button. These should have been "Yes" and "No" respectively.

## Root Cause
All message indices in `chunk_r37_r48_r49_translated.json` and `chunk_r37_extra.json` were off by +1. Every translation was being injected into the WRONG FFFF group -- one position too late.

Evidence:
- R37 decoded text: msg 8 = "bonus point", msg 9 = "はい" (Yes), msg 10 = "いいえ" (No)
- Translation file had: msg 9 = "Bonus Point", msg 10 = "Yes", msg 11 = "No"
- Injection code maps translation msg N -> FFFF group N directly
- Result: "Bonus Point" overwrote the Yes slot, "Yes" overwrote the No slot

This affected ALL entries in both files, not just the buttons:
- R37: 14 entries in main file + 100 entries in extra file (chargen prompts, keyboard layouts, preset names)
- R48: 107 entries (shop/building names)
- R49: 111 entries (dungeon event messages)

## Fix Applied
Subtracted 1 from every `"message"` field in both files:

### chunk_r37_r48_r49_translated.json
- R37 entries: msg 2->1, 3->2, ..., 18->17 (main file)
- R48 entries: msg 1->0, 2->1, ..., 107->106
- R49 entries: msg 1->0, 2->1, ..., 111->110

### chunk_r37_extra.json
- R37 entries: msg 8->7, 13->12, 14->13, 19->18, ..., 126->125

## Verification
After fix, translations now align with decoded text:
- msg 7: EN="Is this OK?" | JP="これでよろしいですか？" -- correct
- msg 8: EN="Bonus Point"  | JP="bonus point" -- correct
- msg 9: EN="Yes"          | JP="はい" -- correct
- msg 10: EN="No"          | JP="いいえ" -- correct

R48 also verified:
- msg 0: EN="None"               | JP="なし" -- correct
- msg 1: EN="Illegal Dump Site"   | JP="不法投棄場" -- correct

## Files Modified
- `data/translate_chunks/chunk_r37_r48_r49_translated.json`
- `data/translate_chunks/chunk_r37_extra.json`

## Impact
This fix corrects ~232 translation placements across three resources (R37, R48, R49). Previously every single one was landing on the wrong message slot. Rebuild required.
