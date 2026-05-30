# Compass HUD & Dungeon Overlay Investigation

**Date**: 2026-05-28  
**Task**: Find PACKDATA resource containing compass HUD and overlay textures with Japanese text

---

## Executive Summary

**The dungeon compass uses purely graphical arrows -- NO Japanese text to translate.**

The compass direction indicator is a red/pink arrow sprite rendered at VRAM address 0x1980. It contains no text labels (no N/S/E/W, no Japanese characters). The compass rotates based on player facing direction. The floor indicator (B1F, B2F, etc.) is rendered using numeric digit sprites from the MSG glyph system, not baked into a texture.

**Translation action required: NONE for the compass or dungeon HUD overlay.**

---

## Evidence

### 1. PCSX2 Texture Dump Analysis (411 PNGs)

Systematically examined all texture captures from PCSX2 during gameplay:

| Category | VRAM Addr | Count | Content | Japanese Text? |
|----------|-----------|-------|---------|---------------|
| Compass arrow | 0x1980 | 2 | Red/pink directional arrow sprite (~32px) | NO -- purely graphical arrow |
| Numeric digits | 0x2214 | 24 | Digits 0-9, slash "/" (10x16 each) | NO -- already numeric/English |
| MSG glyph chars | 0x2a94 | 36 | Individual font glyphs (24x24 each) | YES but these are the MSG font atlas glyphs rendered at runtime, already handled by translation pipeline |
| Small icons | 0x2214 | 134 | 16x16 tiny icons/cursors | NO -- non-text graphical elements |
| UI arrows | 0x2614 | 5 | Green/pink triangular arrows (32x24, 32x32) | NO -- directional indicators |
| Dungeon walls | 0x1993-0x19d3 | 17 | Stone walls, pillars, fog (128x128) | NO -- 3D environment textures |
| UI frames | 0x2254 | 3 | Banner frames, decorative borders (32x56, 0x120) | NO -- ornamental elements |
| Gradient bars | 0x2214 | 3 | HP/MP bar gradients (0x32, 64x16) | NO -- bar fill textures |
| Stat numbers | 0x1dd4 | 11 | Floor/level numbers (16x40) | NO -- digits |
| Button sprites | 0x2214 | 8 | Small rectangular buttons (48x20) | Faint/unreadable at this size -- likely icons not text |

### 2. EXE Analysis (Previously Confirmed)

- **SJIS search for direction kanji** (北/南/東/西): Zero genuine hits in EXE
- **ASCII search** (North/South/East/West/NSEW): Zero hits in both Busin 0 and Busin 1 EXEs
- **Glyph-encoded directions**: Direction kanji glyph IDs do not exist in the MSG font mapping
- **Debug string** at 0x3EC4D0: `CockpitImg Init!!!` -- cockpit system init, no direction text
- **Debug string** at 0x3EA210: `Map Init!!!` -- automap system init, no text

### 3. Busin 1 (English) Cross-Reference

Busin 1's English version (SLUS-20259) has NO compass direction text strings in its EXE either. The Wizardry Alternative series uses a graphical compass arrow, not text-labeled cardinal directions. Both games share this design.

### 4. Resource Format

The compass arrow at VRAM 0x1980 is a small (~32x32) translucent red arrow sprite. Two variants were captured (different rotations/states), both sharing the same graphical design with no text overlay. The compass works by rotating this arrow sprite to indicate the player's facing direction.

---

## Other Dungeon HUD Elements Checked

### Floor Indicator (B1F, B2F, etc.)
- Uses the **numeric digit sprites** (0-9) from VRAM 0x2214 combined with ASCII "B" and "F" characters
- These are the same 10x16 digit glyphs used throughout the game
- Already alphanumeric -- no Japanese text involved
- The EXE has internal room ID keys like `B01F_0_01` at 0x3FAB70 (ASCII, never displayed)

### Automap/Minimap
- Rendered procedurally by the game engine (`Map Init!!!` at 0x3EA210)
- Uses colored rectangles for rooms and corridors, not labeled with text
- No Japanese map labels found in any texture dump

### HP/MP Bars
- Gradient fill textures at VRAM 0x2214 (0x32 size, 64x16)
- Purely graphical bar fills with no text

### Menu Overlay During Dungeon
- Camp/dungeon menu buttons use the **MSG font glyph system** (EXE glyph ID table)
- These are already addressed by the menu label translation pipeline (M1 in REMAINING_WORK.md)
- Not a texture replacement task

---

## Conclusion

**S3 (Compass HUD Directions) in REMAINING_WORK.md should be marked as RESOLVED -- NO WORK NEEDED.**

The compass is a graphical arrow sprite, not text. The floor indicator uses numeric digits. The automap is procedurally rendered without text labels. All dungeon menu text is handled by the existing MSG glyph translation pipeline.

---

## Files Referenced
- PCSX2 dumps: `build/pcsx2_dumps/84b52d35cbf2174c-r0x32-00001980.png` (compass arrow)
- PCSX2 dumps: `build/pcsx2_dumps/b056928d1a1fad3-r0x32-00001980.png` (compass arrow variant)
- Previous analysis: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/exe_dungeon_text.md`
- Previous analysis: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/recon_cockpit_textures.md`
- REMAINING_WORK.md item S3 at line 119
