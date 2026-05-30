# Atlus PS2 Fan Translation Texture/Font Editing Research

**Date**: 2026-05-28
**Purpose**: Survey how fan translators have handled PSMT4 atlas modification in Atlus and Racjin PS2 games, with focus on 1024x1024 PSMT4 textures with PSMCT16 palettes.

---

## 1. Atlus PS2 Texture Format: TMX / SPR

### The Atlus Standard (Persona 3, Persona 4, DDS, Nocturne)

Atlus PS2 games use a proprietary texture format called **TMX** (closely related to Sony's TIM2/TM2). TMX is the standard image format used in Persona 3, Persona 4, Digital Devil Saga, and nearly all Atlus-developed PS2 titles up to Persona 5.

**Key characteristics of TMX:**
- Stored inside SPR (sprite container) or PAC/BIN archives
- Supports PSMT4 (4-bit indexed), PSMT8 (8-bit indexed), and direct-color modes
- Pixel data can be PS2-swizzled (stored swizzled every 0x20 bytes for faster GS rendering)
- Palette data may be CSM1 swizzled (CLUT storage mode 1 interleaving)
- Multiple CLUTs per image supported (palette swapping for UI states)

### Primary Tool: Amicitia

**Amicitia** (by TGEnigma) is the de facto tool for editing Atlus PS2 textures:
- GitHub: https://github.com/TGEnigma/Amicitia
- Supports TMX texture import/export (PNG conversion)
- Handles SPR containers (groups of TMX images for UI/bustups)
- Can open PAC/BIN archives to access nested TMX files
- Supports texture replacement from PNG with automatic format conversion

**Amicitia is Atlus-specific** -- it understands TMX header fields, SPR container structure, and PAC archive layout. It does NOT handle Racjin's proprietary format used in Busin 0.

### Persona 3/4 Modding Pipeline

The established workflow for PS2 Persona texture mods (documented at shrinefox.com):

1. Extract CVM archive using ROFS tool or Mod Compendium
2. Open PAC/BIN/SPR files in Amicitia
3. Export TMX textures as PNG
4. Edit in image editor (respecting palette constraints)
5. Re-import PNG into TMX via Amicitia
6. Rebuild CVM archive
7. Patch ISO with new CVM

This pipeline handles swizzle/deswizzle transparently -- Amicitia manages the PS2 GS format conversion internally.

**Relevance to Busin 0**: LOW. Busin 0 does not use TMX/SPR/CVM. It uses Racjin's proprietary PACKDATA.DIG with GS register block headers. We cannot use Amicitia directly.

---

## 2. Racjin-Specific Texture Handling (Busin 0's Developer)

### The Non-Standard 4bpp Swizzle Problem

A critical finding from ZenHAX forum discussions about Naruto: Uzumaki Chronicles (another Racjin PS2 game):

> "The 4bpp swizzle algorithm of Uzumaki Chronicles is different from [standard]. Other games can be solved by converting to 8bpp and using the 8bpp unswizzle method, but the 4bpp of this game is different. Only Noesis can unswizzle this format."

This was posted by hackers working on Racjin's CFC.DIG texture extraction (ZenHAX thread t=13414, November 2021). The key implications:

1. **Standard PSMT4 deswizzle may not work** for Racjin games
2. The common trick of "treat 4bpp as 8bpp" fails for Racjin's format
3. Noesis has a specific plugin that handles Racjin's variant
4. The non-standard swizzle is specific to the 4bpp path; 8bpp textures use standard GS swizzle

### However: Busin 0 R1272 Uses Standard PSMT4

Our existing `tools/psmt4_deswizzle.py` successfully deswizzles R1272 (256x512 PSMT4) using standard PCSX2 GSTables block/column tables, and the round-trip test passes (deswizzle then reswizzle = exact original bytes). This suggests that:

- Busin 0's PSMT4 swizzle **is standard GS swizzle** (at least for 256x512)
- The non-standard swizzle in Naruto: Uzumaki Chronicles may be a different Racjin sub-team or later development
- OR the non-standard swizzle only manifests at certain dimensions (e.g., 1024x1024)

### Racjin Archive Differences

| Game | Archive | Texture Format | Swizzle |
|------|---------|---------------|---------|
| Naruto: Uzumaki Chronicles 1/2 | CFC.DIG | Raw with sub-pictures | Non-standard 4bpp |
| Fullmetal Alchemist 3 | CFC.DIG | Similar to Naruto | Unknown |
| Busin 0: Wizardry Alternative Neo | PACKDATA.DIG | GS register block headers | Standard (confirmed for 256x512) |
| Wizardry: Tale of the Forsaken Land | Unknown | Unknown | Unknown |

The CFC.DIG extraction script made for Naruto does NOT work on PACKDATA.DIG -- different archive structure entirely.

---

## 3. PSMT4 1024x1024 Deswizzle: Technical Challenges

### Buffer Width (TBW/DBW) for 1024x1024

From the TEX0 register analysis of R1188:
- TEX0 has TBW=16, meaning Texture Buffer Width = 16 * 64 = 1024 texels
- PSM=0x14 (PSMT4), dimensions 1024x1024

For PSMCT32 upload addressing (how the game sends data to VRAM):
- PSMCT32 page = 64x32 pixels
- For a 1024-wide texture uploaded as PSMCT32: dbw_ct32 = 1024/64 = 16 pages wide
- But PSMT4 data packs 2 pixels per byte, so 1024 PSMT4 pixels = 512 bytes per row
- As PSMCT32 pixels (4 bytes each): 512 bytes / 4 = 128 PSMCT32 pixels per row
- So the PSMCT32 upload width = 128, giving dbw_ct32 = 128/64 = 2 pages

Wait -- this depends on how the game uploads. Two scenarios:

**Scenario A: Direct PSMT4 upload (DPSM=PSMT4 in BITBLTBUF)**
- PSMT4 page = 128x128
- 1024/128 = 8 pages wide
- Total pages = 8 * 8 = 64
- Data size = 64 * 8192 = 524,288 bytes (matches R1188's pixel data exactly!)
- TBW=16 means buffer is 16*64=1024 texels wide in PSMT4 address space

**Scenario B: PSMCT32 upload (DPSM=PSMCT32 in BITBLTBUF) -- common for DMA speed**
- PSMCT32 interprets the same bytes as 32-bit pixels
- 524,288 bytes / 4 = 131,072 PSMCT32 "pixels"
- At dbw_ct32=2 (128 pixels wide): height = 131,072/128 = 1024 rows
- At dbw_ct32=4 (256 pixels wide): height = 131,072/256 = 512 rows
- At dbw_ct32=16 (1024 pixels wide): height = 131,072/1024 = 128 rows

The correct dbw_ct32 depends on BITBLTBUF.DBW in the actual DMA chain, which we need to check in the EXE or capture from PCSX2.

### Our Existing Tool's Approach

`tools/psmt4_deswizzle.py` uses the two-phase VRAM simulation:
1. Write raw bytes to VRAM array using PSMCT32 addressing (block/column tables for PSMCT32)
2. Read nibbles from VRAM array using PSMT4 addressing (block/column tables for PSMT4)

For R1272 (256x512): dbw_ct32=256, which means PSMCT32 upload width=256, height=64. This works.

For R1188 (1024x1024): We need to determine the correct dbw_ct32. Options to try:
- dbw_ct32=128 (128 PSMCT32 pixels wide, 1024 rows)
- dbw_ct32=256 (256 PSMCT32 pixels wide, 512 rows)
- dbw_ct32=64 (if buffer is narrower than texture)

### Previous Bruteforce Results

Files in `build/r1188_bruteforce/` show attempts with different header offsets:
- `r1188_psmt4_swizzle_1024x1024_hdr2048.png`
- `r1188_psmt4_swizzle_1024x1024_hdr2128.png`
- `r1188_psmt4_swizzle_1024x1024_hdr3072.png`
- `r1188_psmt4_swizzle_1024x1024_hdr4096.png`

And `build/textures_to_edit/R1188_psmt4_deswizzled.png` exists, suggesting some deswizzle was attempted.

---

## 4. PSMCT16 Palette Format

### Color Layout

PSMCT16 stores each color as a 16-bit value:
- Bits 0-4: Red (5 bits, 0-31)
- Bits 5-9: Green (5 bits, 0-31)
- Bits 10-14: Blue (5 bits, 0-31)
- Bit 15: Alpha (1 bit, 0=transparent or 1=opaque, depends on TEXA register)

To convert to 8-bit per channel: `channel_8bit = (channel_5bit << 3) | (channel_5bit >> 2)`

### CLUT Size for PSMT4 with PSMCT16

- PSMT4 = 16 colors
- PSMCT16 = 2 bytes per color
- Total CLUT size = 16 * 2 = 32 bytes

Compare with PSMCT32 palette:
- 16 colors * 4 bytes = 64 bytes

### CLUT Swizzle (CSM1)

For 8-bit indexed textures (PSMT8), CLUTs stored in CSM1 mode have interleaved entries. The standard CSM1 unswizzle reorders entries in groups of 8.

For 4-bit indexed textures (PSMT4), CSM1 swizzle does NOT apply -- the CLUT is only 16 entries, which fits in a single CLUT row. No interleaving occurs.

### R1188's Palette

R1188 has a real 16-color CLUT with actual RGB values (non-grayscale), stored at offset 0x840-0xBFF. Multiple palette variants exist for different UI states (normal, selected, etc.), enabled by changing CSA (CLUT Start Address) in TEX0 to select among sub-palettes.

---

## 5. Tools Inventory for PS2 PSMT4 Texture Work

### Directly Applicable to Busin 0

| Tool | Type | PSMT4 Support | Notes |
|------|------|--------------|-------|
| `tools/psmt4_deswizzle.py` | Python, custom | Yes (standard GS) | Our tool, verified for 256x512 |
| `tools/psmt4_deswizzle_v2.py` | Python, custom | Yes (page-linear) | Handles .bin format directly |
| PCSX2 texture dump | Emulator | Via GS dump | Can capture deswizzled textures at runtime |
| PS2ImageTool | GUI, C# | Yes | Experimental tool for raw PS2 binary image extraction |

### Reference Implementations (for algorithm verification)

| Tool/Code | Source | Notes |
|-----------|--------|-------|
| Fireboyd78 4-bit unswizzle | [GitHub Gist](https://gist.github.com/Fireboyd78/1546f5c86ebce52ce05e7837c697dc72) | C# code with PSMT4 block/column tables |
| TellowKrinkle GS Swizzle Visualizer | [GitHub Gist](https://gist.github.com/TellowKrinkle/bd6c6e1735cf5e03110ec57ddeea43a9) | Interactive visualizer for all GS PSM modes |
| ResHax C code for 4bpp swizzle | [ResHax Forum](https://reshax.com/topic/696-c-code-to-swizzle-4bpp-ps2-textures/) | C implementation, NFS Carbon PS2 context |
| PCSX2 GSTables.cpp | [PCSX2 Source](https://github.com/PCSX2/pcsx2) | Authoritative block/column tables |
| PS2Linux TextureSwizzling.pdf | [PDF](http://ps2linux.no-ip.info/playstation2-linux.com/download/ezswizzle/TextureSwizzling.pdf) | Original Sony documentation on swizzle theory |

### Atlus-Specific (NOT directly applicable)

| Tool | Purpose | Why Not Applicable |
|------|---------|-------------------|
| Amicitia | TMX/SPR editor for Persona games | Busin 0 doesn't use TMX format |
| PersonaSpriteTools | SPD/SPR editing | Wrong container format |
| Mod Compendium | CVM archive management | Busin 0 uses PACKDATA.DIG, not CVM |
| Rainbow | TIM2/TM2 converter | Busin 0 doesn't use TIM2 |
| OpenKH tools | Kingdom Hearts texture editing | Different game engine entirely |

### General PS2 Texture Tools

| Tool | Purpose | PSMT4? | URL |
|------|---------|--------|-----|
| Console-Swizzler | C library for console texture swizzle | PS2 4bpp/8bpp | [GitHub](https://github.com/matyamod/Console-Swizzler) |
| PS2ImageTool | GUI raw binary image extractor | Yes | [GitHub](https://github.com/Surihix/PS2ImageTool) |
| Noesis + Racjin plugin | Racjin game texture reading | Yes (non-standard) | ZenHAX community |

---

## 6. How Other Fan Translations Handled Font Textures

### Persona 3/4 PS2 Modding (Atlus, reference case)

- Font textures stored as TMX inside SPR containers
- Amicitia handles all format conversion transparently
- Modders export to PNG, edit, re-import
- HD texture packs use PCSX2's texture replacement feature to bypass format issues entirely
- Palette constraints handled by Amicitia's import pipeline

### Growlanser VI (Career Soft / Atlus, PS2)

- Fan translation by Risae (released ~2020, improved 2025)
- Implemented Variable Width Font (VWF) by porting GL5's font system to GL6
- Font renderer code was modified at the EXE level to support 1-byte characters
- The GL5 English VWF table was located and ported to GL6 since both share 90% engine code
- **Key insight**: When the original publisher (Working Designs for GL2/3) already built VWF support, translators can find and reuse that code in sister titles

### SMT: Digital Devil Saga (Atlus, PS2)

- HD texture pack projects reached 98% texture coverage
- Font remained "incomplete with bad dump" -- indicating font atlas extraction is harder than general textures
- Undub mod by Canzah & TGE modified text and audio but likely did not touch font textures
- Text editing tools (AFriendlyIrin/SMT-text-editing on GitHub) focus on text encoding, not texture modification

### trap15's Busin 0 Translation Attempt

- Posted on RPGCodex forums (~2020s)
- Reported "getting all the font renderers mostly wrangled" and making progress on "the town"
- Noted the game is "strangely programmed" and PS2-unfamiliar
- No technical details shared about texture editing approach
- Status appears stalled/incomplete

### General PS2 Translation Pattern

From the romhacking.net PS2 Translation Tutorial (document #919):
1. Extract ISO
2. Find text in binary files (usually SHIFT-JIS encoded)
3. Locate font rendering routine via MIPS disassembly / PCSX2 debugger
4. Modify font width table in EXE for VWF
5. Replace font atlas texture (format-dependent)
6. Rebuild ISO

The texture replacement step (step 5) is the least standardized -- each game uses different formats, and tools must be custom-built or adapted.

---

## 7. Specific Findings for Busin 0's 1024x1024 Problem

### What We Know

1. R1188 is 1024x1024 PSMT4 with PSMCT16 palette (17 sub-entry rendering states)
2. R1272 is 256x512 PSMT4 (standard GS swizzle, verified)
3. Both are uploaded via GS register block headers (not TIM2/TMX)
4. The .raw format is PSMCT32-swizzled (as uploaded to VRAM)
5. The .bin format is page-linear (no GS block swizzle, usable directly)

### Recommended Approach

**For R1272 (main font atlas, 256x512):**
- SOLVED. Standard PSMT4 deswizzle works. Round-trip verified.
- Edit the .bin page-linear format directly for simplicity.

**For R1188 (name entry UI atlas, 1024x1024):**

1. **Determine the correct dbw_ct32 parameter**:
   - Check the BITBLTBUF register in R1188's GS register blocks
   - OR dump the texture from PCSX2 during the name entry screen
   - OR try dbw_ct32 values systematically: 64, 128, 256 (our tool supports this)

2. **If standard PSMT4 deswizzle fails at 1024x1024**:
   - Check if the .bin format already stores page-linear data (no deswizzle needed)
   - Try the Fireboyd78 or ResHax 4bpp implementations as cross-references
   - Use PCSX2's GS dump to capture the exact VRAM state and compare
   - As last resort, try Noesis with Racjin plugin (requires manual plugin setup)

3. **Palette handling**:
   - Parse the PSMCT16 palette at offset 0x840
   - Convert 5-5-5-1 to RGBA for editing
   - When reinserting, convert back to PSMCT16 format
   - Preserve multiple palette variants for UI state switching

4. **Editing workflow**:
   - Deswizzle to PNG (with correct palette applied)
   - Edit Japanese text regions in image editor
   - Reswizzle using inverse of deswizzle algorithm
   - Replace pixel data in resource file (keep headers/palettes intact unless palette change needed)

### The "EA Type 3" 4bpp Swizzle (Tangential but Notable)

A ResHax discussion documents that EA PS2 games use yet another variant of 4bpp swizzle ("type 3"), different from both the standard GS method and Racjin's method. This reinforces that:
- There is no single universal "PS2 4bpp deswizzle" algorithm
- The standard PCSX2 GSTables approach is the most common
- Games may apply additional transforms on top of GS swizzle
- When the standard method works (as it does for R1272), that is the correct algorithm

---

## 8. Summary & Recommendations

### Key Takeaways

1. **Atlus PS2 games use TMX format with mature tooling (Amicitia)** -- but Busin 0 is a Racjin game with a completely different format, so Atlus tools do not apply.

2. **Racjin is known for non-standard 4bpp swizzle** -- but this was specifically documented for Naruto: Uzumaki Chronicles, and our R1272 deswizzle works with standard tables. The non-standard swizzle may be a Naruto-specific quirk.

3. **The 1024x1024 dimension is not inherently problematic** -- TBW=16 is valid for the GS, and the standard PSMT4 block/column tables are dimension-independent. The only variable is dbw_ct32 (PSMCT32 upload buffer width).

4. **PSMCT16 palette is straightforward** -- 16 colors * 2 bytes = 32 bytes, 5-5-5-1 format, no CSM1 swizzle for 4-bit CLUT.

5. **The .bin page-linear format may bypass swizzle entirely** -- if R1188's .bin file stores pre-deswizzled data, we can edit it directly without worrying about VRAM swizzle at all.

### Next Steps (Priority Order)

1. Check if R1188's .bin file is already page-linear (like R1272's .bin)
2. If yes: edit .bin directly, skip swizzle
3. If no: determine dbw_ct32 from GS register blocks and run standard deswizzle
4. If standard deswizzle produces garbage: PCSX2 GS dump comparison
5. Parse PSMCT16 palette and identify which sub-palettes map to which UI states

---

## Sources

### Atlus/Persona Modding
- [Amicitia - Atlus format editor](https://github.com/TGEnigma/Amicitia)
- [Amicitia Wiki - TMX format](https://amicitia.miraheze.org/wiki/TMX)
- [Amicitia Wiki - SPR format](https://amicitia.miraheze.org/wiki/SPR)
- [Amicitia Wiki - CVM format](https://amicitia.miraheze.org/wiki/CVM)
- [PersonaSpriteTools](https://github.com/Secre-C/PersonaSpriteTools)
- [Persona 3/4 PS2 Mod Loading Guide](https://shrinefox.com/blog/2020/03/29/loading-modded-files-in-persona-3-4-ps2/)
- [Persona 3 FES PS2 Mod Support Docs](https://docs.shrinefox.com/getting-started/persona-3-fes-ps2-mod-support)

### PS2 Texture Swizzle Implementations
- [Fireboyd78 4-bit Unswizzle Code](https://gist.github.com/Fireboyd78/1546f5c86ebce52ce05e7837c697dc72)
- [TellowKrinkle GS Memory Swizzle Visualizer](https://gist.github.com/TellowKrinkle/bd6c6e1735cf5e03110ec57ddeea43a9)
- [ResHax: C code to swizzle 4bpp PS2 textures](https://reshax.com/topic/696-c-code-to-swizzle-4bpp-ps2-textures/)
- [ResHax: EA "Type 3" 4-bit swizzle](https://reshax.com/topic/17924-ps2-how-does-ea%E2%80%99s-type-3-4-bit-swizzle-actually-work/)
- [Console-Swizzler C library](https://github.com/matyamod/Console-Swizzler)
- [PS2Linux TextureSwizzling.pdf](http://ps2linux.no-ip.info/playstation2-linux.com/download/ezswizzle/TextureSwizzling.pdf)

### Racjin-Specific
- [ZenHAX: PS2 RAW Texture Format (Racjin Naruto)](http://zenhax.com/viewtopic.php@t=13414.html)
- [ZenHAX: Busin 0 PACKDATA.DIG](http://zenhax.com/viewtopic.php@t=13890.html)
- [Racjin decompression tools](https://github.com/Raw-man/Racjin-de-compression)
- [Naruto UC2 HD Texture Pack (GBAtemp)](https://gbatemp.net/threads/naruto-uzumaki-chronicles-2-slus-21594-ai-upscaled-texture-pack.664299/)

### PS2 GS Technical Documentation
- [ps2tek - PS2 Internals](https://psi-rockin.github.io/ps2tek/)
- [Maister: PS2 GS Emulation](https://themaister.net/blog/2024/07/03/playstation-2-gs-emulation-the-final-frontier-of-vulkan-compute-emulation/)
- [fobes.dev: Palette Shifting with the GS](https://fobes.dev/gs/2024/01/20/palette-shifting-with-the-gs.html)
- [ps2dev: How to swizzle textures](https://forums.ps2dev.org/viewtopic.php?t=3021)
- [ps2dev: Problem with 4-bit Palettised Textures](https://forums.ps2dev.org/viewtopic.php?p=81358)
- [OpenKH: TM2 format documentation](https://openkh.dev/common/tm2.html)
- [PS2ImageTool](https://github.com/Surihix/PS2ImageTool)
- [PCSX2 Source (GSTables)](https://github.com/PCSX2/pcsx2)

### Fan Translation Projects Referenced
- [Growlanser VI English Translation](https://growlanser6english.blogspot.com/)
- [SMT Text Editing Tools](https://github.com/AFriendlyIrin/SMT-text-editing)
- [DDS1 HD Texture Pack (GBAtemp)](https://gbatemp.net/threads/digital-devil-saga-1-usa-hd-remaster.609662/)
- [trap15 Busin 0 discussion (RPGCodex)](https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/page-4)
- [romhacking.net PS2 Translation Tutorial](https://www.romhacking.net/documents/919/)
- [romhacking.net Swizzling Tool](https://www.romhacking.net/utilities/1367/)
- [romhacking.net Rainbow (TIM2 converter)](https://www.romhacking.net/utilities/1069/)
- [Wizardry fan translations wiki](https://wizardry.wiki.gg/wiki/Fan_translation)
