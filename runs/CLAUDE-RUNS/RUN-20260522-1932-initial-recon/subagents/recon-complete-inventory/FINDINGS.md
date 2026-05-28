# Complete Text Inventory - Findings

**Agent**: recon-complete-inventory
**Date**: 2026-05-22
**Output**: `data/COMPLETE_TEXT_INVENTORY.md`

## Key Findings

### 1. The game has text in exactly 5 active sources:

1. **MSG glyph text** (1,168 messages) - 96.7% translated. Custom 16-bit encoding.
2. **Embedded dialogue** (177,086 messages across 510 resources) - NOT started. This is the bulk of the game.
3. **EXE hardcoded strings** (~130 genuine Japanese strings) - Shift-JIS in the binary.
4. **Image-based UI text** (unknown count in 226+ texture resources) - NOT cataloged.
5. **System font atlas** (850+ glyph bitmaps) - Partially in progress.

### 2. Files confirmed to contain NO text:

- **TEMP1.LZH**: Despite the name, this is a 318 MB WAV audio file (2ch, 44100Hz, 16-bit PCM). Zero text.
- **BSN2_0.DSI**: MPEG-2 video (60 MB opening movie). No subtitle streams. No embedded text. SJIS byte-pair hits are uniformly distributed noise from video data.
- **IOPRP254.IMG**: IOP boot image. Hardware initialization only.
- **All .IRX files**: IOP hardware drivers (controller, memory card, sound, MIDI).
- **SYSTEM.CNF**: 54-byte boot config.

### 3. EXE string analysis revealed 3 tiers:

- **109 battle skill strings** (0x3EE9D0-0x3F3470): Allied Action names, formation names, status messages. Player-visible in combat UI. Must translate.
- **5 save/load strings** (0x3F8240-0x3FC790): Memory card labels. Player-visible.
- **15 debug strings** (various): TTY output only. Safe to skip.
- **~900 false positives**: Machine code bytes that happen to decode as SJIS. Not text.

### 4. The embedded dialogue (Category 2) is the project's biggest remaining challenge:

- 510 resources, 177,086 total message entries, ~29,398 dialogue lines
- Same glyph encoding as Category 1 (428 mappings already established)
- Resources range from R29 to R2659
- Top resources have thousands of messages (R2651: 30,508; R1084: 9,117 with 518 lines)
- Many high-message-count resources may be data tables (items/stats) rather than dialogue
- Need to build extraction tooling before translation can begin

### 5. There are 296 MSG-structure resources but only 21 have been decoded:

- 275 MSG resources beyond R34-R49 remain unexamined
- These span R636 through R2876
- May contain additional unique text or may be duplicates/variants

### 6. PACKDATA.DIG contains 2,882 resources across 35+ types:

- type-01: 1,642 resources (game data, MSG text)
- type-02: 617 resources (scenes with embedded dialogue)
- type-03: 226 resources (textures - some contain UI text as images)
- type-04: 201 resources (3D models)
- Remaining types are animation, effects, and system data

## Recommendations

1. **Immediate**: Build a type-02 dialogue extractor using the existing glyph map
2. **Immediate**: Catalog type-03 texture resources to identify which contain text
3. **Short-term**: Decode remaining 275 MSG resources to check for unique content
4. **Medium-term**: Translate the ~29,398 dialogue lines (the bulk of all text)
5. **Medium-term**: Create English replacement textures for UI elements
6. **Low priority**: Patch the 130 EXE strings (straightforward but fiddly)
7. **Skip**: FMV video, audio, system files -- no text content
