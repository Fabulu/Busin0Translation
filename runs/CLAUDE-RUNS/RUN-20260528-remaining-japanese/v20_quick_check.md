# v20 Quick Check Report

**Date:** 2026-05-28
**ISO:** `BUSIN0_EN_v20.iso` (1,274,544,128 bytes)

## PACKDATA Size

- **Size:** 839,833,600 bytes (800.9 MB)
- **Status:** OK (matches expected ~801 MB)

## Overflow Check: Descriptions (MSG 87-148)

**Result: FAIL -- 31 out of 62 descriptions exceed 3 lines**

The overflow fix is NOT working for v20. Many descriptions have 4 lines (3 FFFE line breaks) instead of the maximum 3 lines (2 breaks).

| MSG | Lines | Text |
|-----|-------|------|
| 89 | 4 | lives to hoard gold. / angry if loot is / low. |
| 107 | 4 | hates bloodshed. / mourns fallen / allies. |
| 117 | 4 | gender sets base / stats. men=strong, / women=wise. |
| 118 | 4 | human: high faith / & balanced stats / overall. |
| 119 | 4 | elf: high int & vit / but frail. best / at magic. |
| 120 | 4 | gnome: high faith / & agility. suited / for priests. |
| 121 | 4 | dwarf: slow but / strong with deep / faith. fighters. |
| 122 | 4 | hobbit: small but / agile and lucky. / born thieves. |
| 123-125 | 4 | alignment descriptions (good/neutral/evil) |
| 126-141 | 4 | class descriptions (fighter through clown) |
| 143-145 | 4 | stat descriptions (INT/PIE/VIT) |
| 147 | 4 | stat description (LUC) |

**Total OK (<=3 lines):** 31
**Total overflow (>3 lines):** 31

## Alignment Labels (MSG 150-152)

**Result: WRONG -- labels are shifted/misaligned**

| MSG | Expected | Actual |
|-----|----------|--------|
| 148 | (description) | `good "g"` |
| 150 | `good "g"` | `evil "e"` |
| 151 | `neutral "n"` | `good` |
| 152 | `evil "e"` | `neutral` |

The alignment labels are present but in WRONG positions:
- MSG 150 contains "evil" instead of "good"
- MSG 151 contains "good" (without letter hint) instead of "neutral"
- MSG 152 contains "neutral" (without letter hint) instead of "evil"

This suggests the alignment labels were injected at the wrong offsets, or the message indexing is off by 2 (MSG 148 has what should be MSG 150's content).

## Additional Issues Noted

1. **Fullwidth characters still present:** Several descriptions use fullwidth Latin characters (e.g., `v` renders as a fullwidth v-like glyph). This affects: lives, loves, values, evil, forgive, etc.
2. **Unmapped Japanese glyphs:** Some descriptions still contain Japanese characters (e.g., MSG 123 has `教`, MSG 127 has `３`, MSG 130 has `２`).

## Summary

| Check | Status |
|-------|--------|
| PACKDATA size ~801 MB | PASS |
| Descriptions <= 3 lines | FAIL (31/62 overflow) |
| Alignment labels correct | FAIL (wrong positions) |
| No remaining Japanese glyphs | FAIL (scattered remnants) |
