# Agent Briefing: Busin 0 Wizardry Alternative Neo — English Fan Translation

## Project Overview
We're creating a complete English fan translation patch for the PS2 game "Busin 0: Wizardry Alternative Neo" (SLPM-65378, 2003, Racjin/Atlus). The goal is an xdelta patch against the original Japanese ISO that replaces ALL Japanese text with English.

## Current State (Build v11 — WORKING)
The core translation pipeline is fully functional:
- **12,827+ type-2 dialogue messages** translated and injected with variable-size injection
- **Section 1 opcode patcher** remaps all DISPLAY_TEXT/NAME_REF glyph offsets after injection
- **1,126 type-1 menu/item messages** translated
- **Font atlas** with 94 ASCII glyphs at correct positions (char_code - 0x20 = glyph_id)
- **PACKDATA.DIG rebuild** with 125-sector header preservation (critical!)
- **ISO patching** with directory record size update
- Text displays correctly in-game — full sentences, proper spacing, mixed case

## Architecture

### File Format
- **PACKDATA.DIG**: 2,883 resources, 12-byte TOC entries (sector_offset, sector_count, type_code)
- **Type-02 resources**: Multi-section binary. Section 1 = event scripts, Section 2 = dialogue as BE uint16 glyph streams. FFFF = message end, FFFE = line/page break, FFFD = message boundary.
- **Type-01 resources**: MSG glyph text (menus, items, monsters, stats)
- **Type-15/20/44**: Variant MSG formats with offset tables

### Glyph System
- Game uses `glyph_id = ASCII_code - 0x20` for English
- Space=0, A-Z=33-58, a-z=65-90, digits=16-25, punctuation at standard ASCII positions
- Font atlas: 256×512 PSMT4, 21×42 grid of 12×12 cells
- Font width table in EXE at 0x3DDC48 (NOT used by TextEvent renderer — it uses fixed 12px)

### EXE (SLPM_653.78)
- MIPS R5900 ELF, 4.1MB
- Text renderer functions at VA 0x302000-0x310000 (file 0x202000-0x210000)
- 15+ hardcoded glyph ID tables in data section (0x3B0000-0x3FD000)
- Tables use LE uint16 (not BE like MSG files!)
- EXE virtual address = file_offset + 0x100000 - 0x80 (approximately)

### Key Tools
- `build/build_v9.py` — Main build pipeline (type-1 + type-2 injection + rebuild + ISO)
- `build/rebuild_packdata.py` — PACKDATA.DIG rebuild (MUST use this, not /tmp/ versions!)
- `tools/patch_section1_offsets.py` — Section 1 opcode patcher for variable-size injection
- `tools/inject_type2_dialogue.py` — Type-2 dialogue injector
- `tools/encode_english_text.py` — English text to glyph stream encoder
- `tools/extract_type2_dialogue.txt` — Type-2 dialogue extractor
- `tools/psmt8_deswizzle.py` — Texture deswizzle (partially working)
- `data/english_glyph_table.json` — ASCII glyph mapping
- `data/msg_glyph_map.json` — Japanese glyph decoding (810 entries)
- `data/type2_translated/batch_*.json` — All type-2 translations
- `data/translate_chunks/chunk_*_translated.json` — All type-1 translations

### Known Issues (KNOWN_ISSUES.md)
- M1-M14 documented. Key resolved issues:
  - M12: Variable-size injection works with Section 1 opcode patching
  - Stale PACKDATA from /tmp/ rebuild script — FIXED (moved to build/rebuild_packdata.py)
- Key open issues:
  - Chargen stat labels from EXE, not R38
  - CockpitImg textures need PSMT8 deswizzle→edit→reswizzle
  - Name entry bitmap font labels (glyph IDs 6400+)
  - Personality descriptions overflow (shortened in chunk_r38_fix.json)

### Texture System
- CockpitImg resources (R2118-R2124): PSMT8 format, 16-byte sub-header + 192-byte GS registers + pixels + 1024-byte palette
- CLUT palette swizzle: entries 8-15 swap with 16-23 in each 32-entry block
- Pixel data uses PS2 GS PSMT8 block swizzle (NOT simple linear layout)
- 411 ground truth decoded PNGs in build/pcsx2_dumps/ from PCSX2 texture dump
- Deswizzle lookup table with 1,282 empirical data points generated
- Must build deswizzle AND reswizzle for ISO patching (NOT PCSX2 texture replacement!)
- BUSIN 1 English TMX files available as format reference at extracted_busin1/IMAGE/COCKPIT/

### Critical Lessons (from memory)
1. NEVER put scripts in /tmp/ — they get cleaned and builds silently use stale data
2. Agents MUST use Bash as their FIRST tool call or they lose permission
3. Bash is now in the global allow list (settings.json) — agents should have access
4. All texture work must produce ISO patches, NOT PCSX2 texture replacements
5. The font width tables at 0x3DDC48 might be Metrowerks CRT log2 tables, NOT font data
6. Type-03/06 resources are NOT textures — they're 3D model/scene data. Don't inject into them.
7. R39 (type-15) needs a custom injector (/tmp/inject_r39.py) — the v2 pipeline mishandles it

### Translation Reference
- 460MB English fan guide PDF extracted to data/guide_full_text.txt (577 pages, 1.1MB)
- Guide has complete walkthrough with translated dialogue for cross-reference
- Key character names: Gin Barbus (barkeep), Vera Almohad (knight), Simson, Kunnal, Mott/Hannah (orcs), Lucy (shop owner), Raiman, Guillaume, Belgradno, Vago, Casta, Miri, Melanie, Ortrud, Aoi, Webster, Langobart
- Key locations: Duhan (city), Karman's Labyrinth, Vigger Shop, Luna Light (tavern)
