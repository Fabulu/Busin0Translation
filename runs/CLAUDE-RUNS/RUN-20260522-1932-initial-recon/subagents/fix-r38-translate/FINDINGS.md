# R38 Translation Findings

## Summary

Resource 38 contains 176 messages (message numbers 0-187 with gaps). These cover character creation UI text: stat labels, class names, race names, personality traits, stat descriptions, alignment descriptions, class descriptions, race descriptions, and title/rank strings.

## Status

**Nearly all R38 entries were ALREADY translated** in the existing chunk files:
- `chunk_01_translated.json`: 11 entries (msgs 0-11)
- `chunk_02_translated.json`: 113 entries (msgs 12-116)
- `chunk_03_translated.json`: 52 entries (msgs 117-187)

## New Translation Added

Only **1 message was previously untranslated**:

| Message | Japanese | English | Notes |
|---------|----------|---------|-------|
| 54 | ■武 / | Militant / | Unknown glyph 465 (likely 尚武 = martial/militaristic). Personality trait between Omnitsu (msg 53) and Wasteful (msg 55). |

## Fixes Applied in chunk_r38_fix.json

Corrections from existing translations:

1. **Message 14**: Changed from "Gender" to "Personality" (果性 = 性格/personality, not gender - gender is already msg 11)
2. **Message 82**: Changed from "Stupid" to "Hobbyist" (除味家 = 趣味家/hobbyist, a personality trait about having hobbies)
3. **Message 99**: Fixed description - the original Japanese says happy on failure/crushed on success (contrarian trap trait), translation was already approximately correct

## Output File

Written to: `data/translate_chunks/chunk_r38_fix.json`
- Format: `[{"resource": 38, "message": N, "japanese": "...", "english": "..."}, ...]`
- Contains all 176 R38 entries as a consolidated reference
- All translations respect 18-char/line max for short labels
- Longer description messages use multi-line format with " / " separators

## Terminology Used

- **Stats**: HP, HP/MHP, INT, FTH, VIT, AGI, LCK
- **Races**: Human, Elf, Gnome, Dwarf, Hobbit, Automata (+ Io, Europa as locations/servers)
- **Classes**: Fighter, Thief, Mage, Priest, Ninja, Bishop, Samurai, Alchemist, Gizoku, Monk, Paladin, Dark Knight, Shogun, Knight, High Thief, Omnitsu
- **Alignments**: Good "G", Neutral "N", Evil "E"
- **Combat stats**: Attack, Accuracy, Defense, Evasion
- **Magic types**: Sorcery, Holy Magic

## Coverage Notes

- Message 2 (STR/力) does not exist in the decoded data (gap between msg 1 and msg 3) - likely handled elsewhere or hardcoded
- Messages 25-26, 35-36, 42, 151, 153-156 also don't exist in decoded data (natural gaps in resource numbering)
- Messages 158-187 are already in English in the Japanese source (title/rank strings like "commoner", "hero", etc.) - only capitalization was applied
- Message 164 "clurelty" corrected to "Cruelty", msg 166 "dengerous" to "Dangerous", msg 184 "norble" to "Noble" (typos in original)
