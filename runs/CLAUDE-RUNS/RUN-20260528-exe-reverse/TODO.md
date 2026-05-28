# TODO - Remaining Issues for Busin 0 English Translation

## Priority 1: Blocking / Highly Visible

### T1. Font Atlas Uppercase Fix (IN PROGRESS)
- Uppercase A-Z must be at glyph slots 33-58 (where game expects them via ASCII mapping)
- Currently renders uppercase as hiragana because A-Z were at 112-137 (hiragana range)
- Font atlas regenerated, glyph table updated, awaiting ISO rebuild
- **Status**: Code ready, needs PCSX2 closed for rebuild

### T2. Punctuation Glyph Remapping (IN PROGRESS)
- Period `.` must be at glyph 63 (was `>`, original had `。`)
- Comma `,` must be at glyph 62 (was `=`, original had `、`)
- Dash `-` at glyph 13 (was `'`, original had `−`)
- Colon `:` at glyph 26 (was `/`, original had `：`)
- Apostrophe `'` moved to glyph 29
- Slash `/` moved to glyph 30
- Space `!` rendering issue — glyph 1 should be blank but may have pixels
- **Status**: Glyph table updated, font atlas regenerated, needs rebuild

### T3. Intro Narration is PRE-RENDERED TEXTURE IMAGES (DIAGNOSED)
- The opening slideshow narration ("その悲惨な戦争は...") is NOT glyph-rendered text
- It's stored as pre-rendered texture images displayed via the TextEventImage system
- Characters like 悲惨争役々憶 don't exist in the MSG glyph font at all
- Exhaustive search of entire 1.2GB ISO found ZERO text-encoded matches in any encoding
- EXE has TextEventImageDrawRequest, SetTextEventImageData functions confirming image-based rendering
- **Fix**: Find the texture resources containing the intro text images, create English replacement textures, inject them. This is pixel-art/image editing work, not text encoding.
- **Alternative**: Shorter-term, could overlay English text via a different mechanism or just accept Japanese intro
- **Status**: ROOT CAUSE FOUND — needs texture replacement approach

### T4. Character Creation Screens Garbled
- Name entry: kana grid visible but English letters only at some positions
- Gender/Race/Class selection: first letter of each option shows as hiragana
- Root cause: same as T1 (uppercase at wrong glyph slots) + name entry uses hardcoded kana grid
- Name entry grid fix requires EXE patching (hardcoded glyph ID table)
- **Needs**: T1 fix first, then EXE analysis for name entry grid

### T5. Location Banner Labels Blank
- Top-left location names (tavern, shop, etc.) render as solid colored rectangles with no text
- The glyph IDs for location names point to empty slots in the font atlas
- These are Japanese kanji slots (e.g., 酒場) that we blanked out
- **Needs**: Location name text is in R40 (translated), but the rendering uses original kanji glyph IDs, not our English glyph IDs. The v2 pipeline may not be injecting R40 correctly, OR the game has a separate location label system.

## Priority 2: Missing Translations

### T6. R1198 Early Game Scenes (DONE - needs rebuild)
- 88 messages translated (guild intro, Vera dialogue, tavern narration)
- Translated and injected but user hasn't tested latest build yet

### T7. Untranslated Gap Resources (R1347-R1355)
- R1347: 10 messages (shop dialogue)
- R1348: 8 messages
- R1349: 11 messages (Vigger Friends points)
- R1351: 23 messages (Romi character dialogue)
- R1352: 21 messages (Melanie/Kunnal)
- R1355: 53 messages (story text)
- **Total**: ~126 messages across 6 resources
- **Needs**: Translation + injection

### T8. ~~Untranslated Resources R681-R697~~ (ASSESSED 2026-05-24 - NO DIALOGUE)
- All 5 resources (R681, R683, R687, R691, R697) are binary/graphical data (3D map geometry, textures)
- Section 2 contains sub-container (magic 0x13131313) with large binary chunks, not text
- Original line counts were false positives from binary data matching glyph indices
- **Status**: CLOSED - no translatable content. See `data/type2_translated/batch_gap681.json`

### T9. ~~Untranslated Resources R900-R1000 Range~~ (ASSESSED - NO DIALOGUE)
- R989, R990, R1034: Large dungeon/map type-02 resources (626-632 KB)
- Section 2 contains binary event data (encounter tables, scripting bytecode), NOT dialogue
- The 63/112/109 "dialogue line" counts were false positives from FFFE in binary data
- Max consecutive Japanese glyph run = 6 chars (vs 12+ in real dialogue resources)
- R989/R990 share identical Section 1 (215,568 bytes) = dungeon floor variants
- **Status**: CLOSED -- no translatable text. Placeholder written to `batch_gap989.json`

### T10. Untranslated Resources R1100-R1190 Range
- R1126: 171 dialogue lines
- R1134: 110 dialogue lines
- R1148: 181 dialogue lines
- R1118: 22 dialogue lines
- Potentially significant story content
- **Needs**: Decode, translate, inject

### T11. Late Game Resources
- R2587: 42 dialogue messages
- R2604: 5 messages
- R2659: 2 messages (already in type2_dialogue_full but may not be translated)
- **Needs**: Translate + inject

### T12. Stray Japanese Sentence in Exposition
- User saw one Japanese sentence amid English exposition text
- Likely from an untranslated interleaved resource (R1347-R1355 or similar)
- Couldn't save state — too fast
- **Needs**: Play through with all gap resources translated to verify

## Priority 3: Polish / Quality

### T13. R39 Equipment Menu — Partial Translation
- 84 of 565 messages translated via custom type-15 injector
- Remaining 481 messages show original Japanese
- Equipment screen, status screen, inventory labels
- **Needs**: Translate remaining R39 messages

### T14. R35 Save/Load Menu — Check Translation Quality
- Save/Load UI text patched but needs verification
- Memory card prompts, format warnings, etc.
- **Needs**: Test save/load flow in PCSX2

### T15. Text Overflow in Some Entries
- 13 entries were over 200 chars (fixed/shortened)
- May still have entries that overflow the 18-char line width visually
- **Needs**: In-game visual verification of long text entries

### T16. EXE Save Slot Names
- Patched EXE at `build/patched_type2/SLPM_653.78` but NOT included in ISO
- The EXE is a separate file in the ISO, not in PACKDATA.DIG
- **Needs**: Patch EXE directly in ISO (find SLPM_653.78 extent, overwrite)

### T17. Speaker Name Tags (Green Text)
- FF01/FFF0 control codes preserved for NPC name coloring
- Not verified in-game that green names actually appear
- **Needs**: Visual verification once font is working

### T18. Battle System Text
- Allied Action names, battle messages ("Dispel Success!", etc.)
- 109 strings identified in EXE at 0x3EE9D0-0x3F3470
- These are debug/TTY strings, likely NOT player-visible
- **Needs**: Verify in battle — if visible, patch EXE

### T19. Remaining MSG Resources (275 type-01)
- Full scan found zero with real Japanese dialogue text
- All are binary data tables
- **Status**: CLOSED — no action needed

## Architecture Issues

### A1. PACKDATA Size Growth
- Current v3 PACKDATA is ~325KB larger than original
- Fits in ISO by updating directory record size
- Risk: if we add more resources, could exceed available space
- **Monitor**: Track size delta with each rebuild

### A2. Type-15 Format Not Fully Understood
- R39 uses type-15 with sequential table + offset table + glyph stream
- v2 pipeline misparses this format (causes extra FFFF)
- Custom injector works but doesn't update offset table
- **Needs**: Full reverse-engineering of type-15 format for proper offset table rebuild

### A3. Type-20/Type-44 Format Edge Cases
- R34 (type-20) and R2654 (type-44) injected by v2 pipeline
- Seem to work but not thoroughly tested
- **Needs**: Verify these resources render correctly in-game

### A4. Multiple Font Atlas Sizes
- EXE has 4 font width tables (248 entries each)
- Different text contexts may use different sizes
- Our atlas only has one size of glyphs
- **Needs**: Investigate if different text sizes need different atlas regions
