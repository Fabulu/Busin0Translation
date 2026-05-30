# Half-Width Font Impact Analysis: 12px to 6px Advance

**Date:** 2026-05-28  
**Question:** Can we use different advance values for different glyph ranges?

---

## Answer: NO -- The Advance Is Global (Uniform for All Glyphs)

The text renderer uses a **fixed 12-byte glyph slot stride** applied uniformly to every glyph. There is **no per-glyph width table** and **no conditional branching based on glyph ID** in the advance logic.

### Evidence

From the renderer analysis (`analysis_text_renderer.md`):

1. **KEY FINDING 2** states explicitly: "The renderer does NOT look up per-glyph widths from a table -- it uses a fixed 12-byte slot structure for all glyphs (both Japanese kanji and any ASCII substitutes)."

2. The `+12` advance appears at **14 locations** in the EXE. Three are display-side pixel advances (0x303E70, 0x303EF4, 0x305BF8) and the rest are struct strides through resource tables.

3. The centering calculation at VA 0x305980 computes `char_count * 24` (i.e., `count * 3 * 8`), confirming every glyph is treated as the same width. There is no glyph-ID lookup in the centering path.

4. The glyph scan (Region B at `0x3B3690`) found a "Glyph Width/Repeat Table" with ~200 bytes of paired kanji glyph IDs, but this was determined to be **rendering metadata** (possibly kerning/display hints), not a per-glyph advance table. It is not referenced in the advance loop.

### What Happens If We Change +12 to +6 Globally

| Glyph Range | Current (12px) | After Change (6px) | Impact |
|-------------|----------------|---------------------|--------|
| ASCII (0-94) | Too wide, wastes space | Correct for half-width Latin | GOOD |
| Kanji (95-682) | Correct for 12x12 CJK | Half-width, overlapping/crushed | BROKEN |
| Menu tiles (683-866+) | Correct for 12x12 word-halves | Tiles overlap, labels unreadable | BROKEN |

**Changing the advance to 6px globally would break ~790 glyph positions** (everything above ID 94).

---

## Options for Per-Range Width

### Option 1: EXE Code Injection (Add Conditional)

Inject a branch in the advance loop that checks the glyph ID:

```
; At VA 0x303E70 (display advance)
; Replace: addiu $v0, $v0, 12
; With:    jal   halfwidth_check
;          nop

; halfwidth_check (injected at free EXE space):
;   lh  $t0, 0($v0)       ; load glyph_index from current slot
;   slti $t1, $t0, 95     ; if glyph_id < 95 (ASCII range)
;   bne $t1, $zero, ascii
;   addiu $v0, $v0, 12    ; default: full width
;   jr $ra
;   nop
; ascii:
;   addiu $v0, $v0, 6     ; half width for ASCII
;   jr $ra
;   nop
```

**Difficulty:** HIGH  
- Must find free space in the EXE for the injected function  
- Must patch all 3 display-side advance sites  
- Must also patch the centering calculation to be glyph-aware  
- Risk of breaking the scroll/animation timing  

### Option 2: Redesign Menu Tiles for 6px Advance (If Going All-6px)

If the advance is changed globally to 6px:
- Menu tiles would need to be redesigned as **4 tiles** instead of 2 (each tile now 6px wide)
- The EXE menu struct only has 2 glyph slots per button -- would need struct expansion
- Kanji would render at half-width -- all 588 kanji glyphs would need to be redrawn at 6x12
- This is essentially a complete font system overhaul

**Difficulty:** EXTREME -- not practical

### Option 3: Keep 12px Advance, Pack 2 ASCII Chars Per Glyph Cell (Current Approach)

This is what the project already does:
- Each 12x12 font cell contains 2 narrow Latin characters (~5-6px each)
- Menu tiles contain half-words ("tav" + "ern") pre-rendered at 12x12
- The advance stays at 12px, but each cell carries more visual content
- Truncation is managed by line-breaking at the MSG build stage

**Difficulty:** ALREADY IMPLEMENTED  
**Limitation:** Max ~36 visual characters per line (18 glyph slots * 2 chars/slot), but the 32-slot parser limit caps it at 32 slots = 64 visual characters (more than enough).

### Option 4: Proportional Width Table (Best Quality, Hardest)

As described in the renderer analysis (Option B):
- Build a 679-byte per-glyph width table in free EXE space
- Hook the advance code to load `width_table[glyph_index]` instead of fixed 12
- ASCII glyphs get width 6, kanji get width 12, menu tiles get width 12
- Requires code injection at 3+ sites plus the centering calculation

**Difficulty:** HIGH but cleanest result

---

## Recommendation

**Do NOT change the advance to 6px globally.** It would break kanji and menu tiles with no easy fix.

The current approach (Option 3 -- packing 2 Latin characters per 12px glyph cell) is already working and avoids all EXE patching. The text truncation problem is addressed by:

1. Pre-wrapping English text at the MSG build stage (18 glyph slots per line)
2. Using newline (0xFFFE) and page break (0xFFFD) codes to flow text across lines/pages
3. The 12x12 cells with 2-char packing give ~36 visible characters per line -- adequate for English

If proportional width is ever desired in the future, Option 4 (per-glyph width table via code injection) is the correct path. Option 1 (simple conditional on glyph ID < 95) is a simpler intermediate step but still requires EXE hacking.

---

## Summary Table

| Approach | ASCII | Kanji | Menu Tiles | EXE Patches | Feasibility |
|----------|-------|-------|------------|-------------|-------------|
| Global 6px | Good | BROKEN | BROKEN | 3 sites | Bad |
| Conditional (ID < 95) | Good | Good | Good | 3 sites + injection | Medium |
| 2-char packing (current) | Good | Good | Good | None | Already done |
| Proportional table | Best | Good | Good | 3 sites + injection + table | Hard |

**Bottom line:** The renderer has ONE global advance for all glyphs. Per-range width requires code injection. The current 2-char packing approach sidesteps the problem entirely and is the recommended path.
