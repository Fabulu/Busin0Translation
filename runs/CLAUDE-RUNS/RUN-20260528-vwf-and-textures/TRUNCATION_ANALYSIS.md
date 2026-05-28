# Text Truncation Deep Analysis (2026-05-28)

## Key Finding: Truncation is NOT a fixed character limit

- msg569 (52 glyphs, 45 visible chars) displays FULLY — all 3 lines
- msg570 (49 glyphs, 21 visible chars) TRUNCATES — only 2 lines, line 2 cut short
- Both in the same DISPLAY_TEXT span (off=26469 cnt=313)
- Both have identical structure: ASCII glyphs + FFFE line breaks
- No special control codes in either

## What's been tried
- X-advance 24→14: Text smaller, SAME truncation point (still 21 chars for msg570)
- Text box width 140→255: NO effect on narration text
- div-by-21→div-by-42: Garbled text (shared with atlas UV lookup)
- DISPLAY_TEXT GLYPH_COUNT: Verified correct, covers full messages
- Font width table: NOT used by TextEvent renderer

## Current Hypothesis
The display buffer has ~42 slots. Messages within a DISPLAY_TEXT span share the buffer.
msg568 uses 50 slots, but renders on its own (first page, player presses button).
msg569 uses 52 slots, renders fully (second page).
msg570 uses 49 slots but only 21 visible — maybe buffer not properly recycled?

OR: Each FFFF-delimited message gets its own render cycle and the buffer DOES reset.
In that case, msg570's 49 glyphs should all show. But they don't.
Something specific to msg570 causes truncation.

## ROOT CAUSE FOUND (2026-05-28 late session)

**The PACKDATA rebuild script was in /tmp/ which got cleaned. ALL builds v8-v10 had the ORIGINAL Japanese Section 2 data, NOT our patched English.** The "truncation" was literally the original 22-word Japanese message being displayed through our English font atlas.

Fixed: rebuild script moved to `build/rebuild_packdata.py`. v11 ISO has verified patched R1196 (sec2_size=86128).

### Additional discovery: Opcode 0x0014 (TEXT_CONTINUE)
- Format: `0x0014, choice_index, 0xFFFF, 0x0000, sec2_offset, 0x0000, byte_count`
- Chains additional text after DISPLAY_TEXT spans
- The Section 1 patcher does NOT handle this opcode yet — needs to be added
- May cause truncation for specific branching dialogue choices

## What we HAVE:
- Advance patch WORKS (text is visually smaller/tighter)
- Text box width patches DON'T affect narration overlay text
- div-by-21 CAN'T be changed (shared with atlas UV)
- Full MIPS disassembly tools available (rabbitizer, spimdisasm)
- PCSX2-MCP debugger available (can set runtime breakpoints)
- Complete function mapping of the text renderer

## What's NEEDED:
- Runtime debugging: Set a breakpoint at the FFFE handler in func_302DB0 to see what happens
  when msg570 processes. Watch the character counter ($s2) and line counter ($s1).
- OR: Examine the ORIGINAL Japanese messages 569 and 570 — maybe the Japanese version of
  msg570 was shorter and the game has per-message metadata limiting display size
- OR: The DISPLAY_TEXT opcode might have DIFFERENT parameters for each message within the span
