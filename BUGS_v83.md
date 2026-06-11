# v83 Bug Report — First Town Playtest (2026-06-11)

Build: BUSIN0_EN_v83.iso (commit 0d30f6e)
Tester: Fabian, fresh boot, PCSX2

## CRITICAL — Game-breaking

### BUG-1: Narration replays on tavern exit
- **Symptom**: Leaving the tavern triggers the post-chargen intro narration again
- **Screenshot**: 202546.png
- **GS dump**: 202546.gs.zst (6MB)
- **Likely cause**: Section 1 opcode patching in a type-02 scene resource shifted trigger offsets, causing the "enter town" narration to re-fire on tavern exit. Or the R1193/R1194 trailing data changes affected scene flow.

### BUG-2: Character portraits missing
- **Symptom**: Dialogue scenes show no character art (should be large portrait filling half screen)
- **Screenshot**: 201255.png (dialogue with "ge y" name), 201630.png (sister dialogue)
- **GS dump**: 201255 area
- **Likely cause**: Type-02 scene resources lost binary data (portrait display commands) during section 2 rebuild. The trailing data fix may not cover all cases, or section 1 opcode patching shifted portrait display commands.

### BUG-3: Character names garbled in dialogue
- **Symptom**: Name label bar shows garbage ("ge y", "rc:") instead of character names
- **Screenshots**: 201255.png, 201630.png
- **Likely cause**: Section 1 SET_NAME_REF opcodes point to wrong section 2 offsets after translation injection. The name references index into section 2 glyph data, and when text grows, the remapped offsets may be wrong.

## HIGH — Affects readability

### BUG-4: Glyph artifacts on r, y, V
- **Symptom**: Lowercase `r`, lowercase `y`, uppercase `V` have stray pixel marks (subscript dots on r/y, overbar on V)
- **Screenshots**: All narration screenshots (200937, 201059, 201141)
- **Likely cause**: R1272 font atlas — Consolas 10pt rendering produces descenders/ascenders that bleed into neighboring cell rows in the 12x12 grid. Or original Japanese glyph data wasn't fully cleared before rendering English.

### BUG-5: Quest descriptions untranslated (REQUEST LIST)
- **Symptom**: Job/quest detail screen shows full Japanese text
- **Screenshot**: 202129.png
- **Resource**: R46 quest descriptions — translations exist in chunk files but the quest detail view may read from a different section or resource than what we patched.

### BUG-6: Bulletin board text overflow/clipping
- **Symptom**: Text overflows left boundary, first 1-2 chars of each line cut off, lines overlap
- **Screenshots**: 202335.png ("board is open" post)
- **GS dump**: 202335.gs.zst
- **Likely cause**: English text is wider than Japanese per line. The R46/R47 bulletin board renderer has a fixed-width text area. Translations need shorter line wraps, or the text area coords need adjusting.

### BUG-7: Bulletin board first character missing
- **Symptom**: First letter of bulletin posts cut off ("ill" instead of "I'll", "board" instead of "A board")
- **Screenshot**: 202227.png
- **Likely cause**: The bulletin board text renderer starts drawing at an X position that clips the first character. May be related to how the offset table points to the start of each message.

## MEDIUM — Cosmetic/incomplete

### BUG-8: Town hub buttons still Japanese
- **Symptom**: 酒場, 依頼, 王国掲示板, etc. — all menu buttons show original kanji
- **Screenshot**: 201746.png, 201958.png
- **Likely cause**: Menu tile glyph IDs 683+ are in the R1272 atlas but the game may read these tiles from a cached/different VRAM location, or the tile rendering system doesn't use R1272 at all for these positions.

### BUG-9: Tavern sub-menu buttons Japanese
- **Symptom**: 依頼, 王国掲示板, 達成履歴, トラップゲーム, 外に出る — all Japanese
- **Screenshot**: 201958.png
- **Likely cause**: Same as BUG-8, or these are a different rendering system (not MSG glyph tiles).

### BUG-10: Bottom bar Japanese
- **Symptom**: キャンプ, システム, ライブラリー controller hints still Japanese
- **Screenshot**: 201958.png
- **Likely cause**: These are likely hardcoded SJIS strings in the EXE or rendered from a different resource.

## Available GS dumps for analysis
- 201746.gs.zst — town hub selection
- 201958.gs.zst — tavern menu
- 202031.gs.zst — tavern menu alt
- 202129.gs.zst — quest description
- 202227.gs.zst — bulletin board (working post)
- 202335.gs.zst — bulletin board (broken post)
- 202546.gs.zst — narration replay on tavern exit

## Priority order
1. BUG-1 (narration replay) — game flow broken
2. BUG-2 + BUG-3 (portraits + names) — dialogue unplayable
3. BUG-4 (glyph artifacts) — every English text affected
4. BUG-5 (quest descriptions) — core gameplay content
5. BUG-6 + BUG-7 (bulletin board) — text layout
6. BUG-8-10 (Japanese buttons) — cosmetic but visible everywhere
