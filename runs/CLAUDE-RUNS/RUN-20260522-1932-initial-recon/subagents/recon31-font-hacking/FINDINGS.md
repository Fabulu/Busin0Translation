# PS2 Font Hacking & Text Rendering Research for Fan Translation Projects

## 1. PS2 Fan Translation Font Replacement Techniques

### How PS2 Games Store Fonts
- **Bitmap font atlases**: Most PS2 games store fonts as bitmap texture atlases -- a single texture image containing all glyphs arranged in a grid or sequential layout. An accompanying data structure (in the ELF or a separate file) describes the position/size of each glyph.
- **TIM2 (.tm2) format**: The standard PS2 image format for textures, including fonts. Supports 4-bit indexed (16 colors), 8-bit indexed (256 colors), 16/24/32bpp direct color. Tools like **Rainbow** and **Textures Extractor/Reinserter** can extract/reinsert TIM2 images from game files.
- **4-bit CLUT (Color Lookup Table)**: The majority of PS2 games use 4-bit CLUT textures for fonts. This gives 16 colors per glyph, typically just foreground/background/anti-aliasing shades. Palette data may be swizzled (CSM1 / CLUT storage mode 1).
- **PS2 texture swizzling**: Pixel data is swizzled every 0x20 bytes for faster GS rendering. This must be accounted for when extracting/reinserting font textures. C code for unswizzling 4bpp textures is documented on ResHax.

### Text Encoding
- **Shift-JIS**: Most Japanese PS2 games use Shift-JIS encoding for text. PS2 BIOS revisions use variations that differ from standard SJIS, with slightly offset character positions.
- **Font tables**: Simple text files mapping hex codes to font characters. Each hex value in the game ROM corresponds to a glyph position in the font texture. Tools like **Cartographer** (dumping), **Atlas** (insertion), and **abcde** (combined) work with these tables.
- **Custom encodings**: Some games use non-standard encodings that require custom character mappings to be reverse-engineered.

### Font Replacement Workflow
1. Locate the font texture file(s) in the game's filesystem (often inside .DAT archive files)
2. Extract using appropriate tools (comptoe for Tales games, quickBMS for general use)
3. Convert TIM2 to editable format (PNG) using Rainbow or similar
4. Replace Japanese glyphs with English glyphs, maintaining the same texture dimensions and bit depth
5. Update the font table/mapping data in the ELF or data files
6. Reinsert the modified texture back into the game archive
7. Rebuild the ISO

### Key Tutorial
- **Romhacking.net PS2 Translation Tutorial** ([romhacking.net/documents/919/](https://www.romhacking.net/documents/919/)) -- the primary community tutorial for PS2 translation hacking.

---

## 2. Variable Width Font (VWF) Implementations on PS2

### The Core Problem
Japanese games typically use fixed-width fonts (monospaced) since CJK characters are naturally uniform in width. English text looks poor in fixed-width unless VWF is implemented, as characters like 'i' and 'W' need different widths.

### How VWF Works (General Pattern)
1. **Width table**: A byte array where each entry specifies the pixel width of each character glyph
2. **X-position advance**: After rendering each character, the X cursor advances by the character's width (from the table) rather than a fixed constant
3. **Code injection**: The game's text rendering routine is patched to:
   - Look up the current character in the width table
   - Use that width value instead of the hardcoded constant
   - Advance the X position by the looked-up width

### VWF on PSP/PS2 (MIPS-based consoles)
From the GBAtemp PSP VWF tutorial (directly applicable to PS2 MIPS):
1. **Find where the constant width is added to X position** for the next letter
2. **Trace back** to where this width value was loaded
3. **Extend the executable** (ELF) to add space for extra code and character width table
4. **Inject code** at the character load point to save a new width value by comparing the character to a width lookup table

### Growlanser 5/6 Case Study (PS2)
- A VWF table was discovered in Growlanser 5 (officially localized by Atlus USA)
- VWF table location in GL5 ELF: **0x314C68**, with 1-byte width values per character
- To modify a letter's width: add its hex value to the table base address
- The GL5 VWF code was ported to GL6 (fan translation) since the engines are ~90% identical
- **Armips** assembler was used to inject VWF code into the ELF file
- Font file: `0000002e.fnt` in both GL5 and GL6

### Atlus Official Localizations
- Atlus USA implemented VWF in their PS2 localizations (Growlanser series, Persona series)
- They used thin but readable fonts optimized for the target platform
- Technical limitations sometimes prevented using different typefaces where the Japanese original had no distinction
- Sprite primitive rendering bugs were encountered: characters stretched because sprites must use even values for u0 coordinate in 4bpp mode

---

## 3. PCSX2 Debugging for Font/Text

### PCSX2 Debugger (Built-in)
- **Access**: Tools > Show Advanced Settings > Debug > Open Debugger
- **Memory Search**: Search for values in memory, filter/refine results
- **Breakpoints**: Break-on-read and break-on-write at specific addresses
- **Registers**: View/modify R5900 (EE) and R3000 (IOP) MIPS registers
- **Disassembly**: Full MIPS disassembly view with step-through capability
- **Memory Editor**: Hex view of PS2 memory with direct editing

### Texture Dumping & Replacement System
- **Enable dumping**: Right-click game > Properties > Graphics > Texture Replacements > Dump Textures
- **Folder structure**: `textures/<GAME_ID>/dumps/` and `textures/<GAME_ID>/replacements/`
- **Load replacements**: Settings > Graphics > Texture Replacement tab > tick "Load Textures"
- **Warning**: Do NOT enable both dump and load simultaneously (performance issues)
- **Known issue**: Some font textures may not load as replacements correctly
- **File formats**: DDS-RGBA recommended for HUD elements, PNG for artwork, DDS-BC7 for general textures

### GS Dump System
- Captures exact Graphics Synthesizer commands during emulation
- Can be replayed for debugging graphics issues without running the full game
- Useful for analyzing how font textures are uploaded and rendered

### GSdx Debug Features
- Debug options in Graphics Settings > Advanced/Debug
- Texture dumping creates many files (SSD wear warning)
- VRAM usage statistics: total VRAM, targets, sources, hash cache, pool

### PCSX2-MCP (AI-Powered Debugging)
- GitHub: [hkmodd/PCSX2-MCP](https://github.com/hkmodd/PCSX2-MCP)
- Exposes PCSX2 debugging via MCP protocol
- Set breakpoints, read registers, disassemble MIPS, inspect memory from an AI coding assistant
- Custom PCSX2 build with integrated DebugServer
- Supports 128-bit registers, native disassembly

### Strategy for Finding Font Loading Code
1. **Texture dump approach**: Enable texture dumping, play until text appears, find the font texture in dumps
2. **Memory search**: Search for known text strings in memory to find text buffer locations
3. **Breakpoint on text buffer**: Set break-on-write on the text buffer address to find the text processing code
4. **Trace rendering**: From the text processing code, follow calls forward to find the GS texture upload and rendering code
5. **GS register watch**: Monitor TEX0 register writes (sets texture base pointer, width, format) to catch font texture uploads

---

## 4. PS2 Text Rendering -- Common Patterns

### How PS2 Games Render Text (Technical Flow)
1. **Font texture uploaded to GS VRAM**: The font bitmap is uploaded once (or per-scene) to GS local memory via DMA channel 2 (PATH3)
2. **GIF packet construction**: For each character, a GIF packet is built containing:
   - PRIM register: set to SPRITE mode with TME (Texture Map Enable) = 1
   - TEX0 register: specifies the font texture base pointer, buffer width, pixel format (PSM), texture size
   - UV coordinates: specify which portion of the font atlas corresponds to this glyph
   - XY coordinates: specify where on screen to draw this character
3. **Rendering**: The GS rasterizes each character sprite using the font texture

### Key GS Registers for Text
- **TEX0**: Texture Base Pointer (TBP0), Buffer Width (TBW), Pixel Storage Format (PSM), texture dimensions
- **CLUT**: Color Lookup Table address and format (for 4/8-bit indexed textures)
- **PRIM**: Primitive type (SPRITE for text), TME flag
- **UV/ST**: Texture coordinates for glyph selection

### Common MIPS Assembly Patterns for Text Rendering
```
# Typical character rendering loop pattern:
# 1. Load character code from string buffer
lbu     $t0, 0($s0)        # Load byte (character) from string pointer
# 2. Calculate glyph position in font atlas
sll     $t1, $t0, 4         # Multiply by glyph width (shift left)
# 3. Calculate UV coordinates
andi    $t2, $t1, 0xFF      # U = (index % chars_per_row) * glyph_width
srl     $t3, $t1, 8         # V = (index / chars_per_row) * glyph_height
# 4. Set up GIF packet with sprite coordinates
sw      $t2, offset($sp)    # Store U coordinate
sw      $t3, offset($sp)    # Store V coordinate
# 5. Advance cursor position
addiu   $s1, $s1, CHAR_WIDTH  # Fixed width advance (VWF replaces this)
# 6. Advance string pointer
addiu   $s0, $s0, 1          # Next character
```

### Tracing from Displayed Character to Glyph Index
1. **Find the text string in memory** (search for known hex values of displayed characters)
2. **Set break-on-read** at that address to find the code that reads the character
3. **The reading code** will contain the glyph index calculation (character code -> atlas position)
4. **Follow forward** to find UV coordinate setup and GIF packet building
5. **The font texture base pointer** in TEX0 tells you where the font atlas lives in GS VRAM

### PS2 Font Texture Formats in Practice
- **4bpp indexed** (most common for fonts): 16 colors, palette-based, highly compact
- **8bpp indexed**: 256 colors, used for anti-aliased or multi-colored fonts
- Font textures are typically 256x256 or 512x256 pixels
- Glyph sizes: commonly 16x16, 12x12, or 8x8 pixels for Japanese; may need adjustment for English

---

## 5. Similar PS2 Translation Projects That Solved Font Issues

### Tales of Destiny 2 (PS2) -- lifebottle Project
- **GitHub**: [lifebottle/Tales-of-Destiny-2](https://github.com/lifebottle/Tales-of-Destiny-2)
- **Font handling**: Pointer table starts at 0x44, referencing the font as the first file in the package
- **Compression**: PS2 version uses LZSS + RLE mixture; PSP version uses zLib
- **Tools**: PyTOD2 (GUI for unpacking/repacking), **comptoe** (compression/decompression, works across Tales PS1/PS2/PSP games)
- **Font select feature**: Patch offers pixel font (PSP/Vita optimized) or hi-res font (PS2/emulator optimized)
- **Challenges**: ASM hacks needed for lowercase fonts, in-battle string limits, menu box expansion, full-width to variable-width character adjustments

### Tales of Destiny Director's Cut (PS2) -- lifebottle Project
- **GitHub**: [lifebottle/Tales-of-Destiny-DC](https://github.com/lifebottle/Tales-of-Destiny-DC)
- Uses the same comptoe compression tools
- Similar font handling approach to ToD2

### Growlanser VI: Precarious World (PS2)
- **Blog**: [growlanser6english.blogspot.com](https://growlanser6english.blogspot.com/)
- **VWF ported from GL5**: Atlus USA's official VWF table from Growlanser 5 was reverse-engineered and ported
- **Font file**: `0000002e.fnt` (same in GL5 and GL6)
- **Armips assembler** used to inject VWF code into the ELF
- **Modified files**: SLPM_667.16 (VWF code + text), GL6_FILE.DAT (menus + font), GL6_SCEN.DAT (script)
- **ISO tools**: Xpert (ISO unpack/repack), quickBMS (DAT extraction)

### Wizardry Series Fan Translations
- Existing fan translations exist for Wizardry Llylgamyn Saga, Wizardry V, Wizardry I-II-III, Wizardry Chronicle
- Font modifications included adding lowercase fonts and cleaning up garbage tiles
- Fan translation wiki: [wizardry.wiki.gg/wiki/Fan_translation](https://wizardry.wiki.gg/wiki/Fan_translation)

---

## 6. Key Tools Reference

| Tool | Purpose | URL |
|------|---------|-----|
| **Rainbow** | TIM2 texture format converter (multi-CLUT, swizzle support) | [romhacking.net/utilities/1069/](https://www.romhacking.net/utilities/1069/) |
| **Textures Extractor/Reinserter** | Scan files for TIM2 images and extract them | [romhacking.net/utilities/659/](https://www.romhacking.net/utilities/659/) |
| **comptoe** | Compressed file pack/unpack for Tales series games | [github.com/lifebottle/comptoe](https://github.com/lifebottle/comptoe) |
| **Armips** | MIPS assembler for injecting ASM patches into ELF files | Community standard for PS2 ASM hacking |
| **Cartographer** | Text dumping from ROMs using table files | Romhacking.net |
| **Atlas** | Text insertion into ROMs using table files | Romhacking.net |
| **abcde** | Combined text dump/insert tool (replaces Cartographer+Atlas) | Romhacking.net |
| **quickBMS** | Generic game archive extractor with scripting | Community standard |
| **Xpert** | PS2 ISO unpack/repack | Community standard |
| **fontengine** | PS2 font library (homebrew) | [github.com/F0bes/fontengine](https://github.com/F0bes/fontengine) |
| **gsKit** | PS2 Graphics Synthesizer C interface with font support | [github.com/ps2dev/gsKit](https://github.com/ps2dev/gsKit) |
| **PCSX2-MCP** | AI-powered PCSX2 debugger bridge | [github.com/hkmodd/PCSX2-MCP](https://github.com/hkmodd/PCSX2-MCP) |

---

## 7. Recommended Approach for This Project

### Phase 1: Identify the Font System
1. Use PCSX2 texture dumping to capture all textures while text is displayed
2. Identify the font atlas texture(s) among the dumps
3. Search the game ISO for TIM2 files using Textures Extractor/Reinserter
4. Locate the font data structures (glyph metrics, width table) in the ELF or data files

### Phase 2: Reverse Engineer Text Rendering
1. Use PCSX2 debugger to search memory for known text strings
2. Set break-on-read breakpoints to find the text processing code
3. Trace forward to find the glyph index calculation and rendering code
4. Document the character encoding (likely Shift-JIS variant or custom)
5. Identify if VWF already exists or if fixed-width rendering is used

### Phase 3: Implement Font Replacement
1. Create English font atlas matching the original's dimensions and bit depth
2. Build a font table mapping ASCII values to glyph positions
3. If VWF needed: inject width table and patch the X-advance code using Armips
4. Handle any texture swizzling requirements
5. Test with PCSX2 texture replacement first (quick iteration) before modifying the ISO

### Phase 4: Integration
1. Replace the font texture in the game files
2. Update encoding tables
3. Patch the ELF with any ASM modifications (VWF, string length limits, text box sizing)
4. Rebuild the ISO and test

---

## Sources

- [Romhacking.net PS2 Translation Tutorial](https://www.romhacking.net/documents/919/)
- [PSP ASM Hacking for Variable Width Font (GBAtemp)](https://gbatemp.net/threads/psp-asm-hacking-for-variable-width-font.374967/)
- [Growlanser VI Translation Blog](https://growlanser6english.blogspot.com/)
- [Tales of Destiny 2 Translation (GitHub)](https://github.com/lifebottle/Tales-of-Destiny-2)
- [PCSX2 Debugger Documentation](https://pcsx2.net/docs/advanced/debugger/)
- [PCSX2 GSdx Debug Wiki](https://wiki.pcsx2.net/PCSX2_Documentation/GSdx_Debug)
- [PCSX2 Texture Dump/Replace PR](https://github.com/PCSX2/pcsx2/pull/5547)
- [PCSX2 Texture Replacement Tutorial (ModDB)](https://www.moddb.com/tutorials/pcsx2-qt-texture-replacement-tutorial)
- [PS2 Graphics Synthesizer Wiki](https://www.psdevwiki.com/ps2/Graphics_Synthesizer)
- [PS2 Font Rendering Tutorial (Dr. Fortuna)](http://ps2-edu.tensioncore.com/old/font/font.html)
- [TIM2 Format Documentation (RE Wiki)](https://rewiki.miraheze.org/wiki/TM2_TIM2_Image)
- [Rainbow Texture Converter](https://www.romhacking.net/utilities/1069/)
- [PS2 Retro Reversing](https://www.retroreversing.com/ps2)
- [fontengine PS2 Library](https://github.com/F0bes/fontengine)
- [gsKit PS2 Graphics Library](https://github.com/ps2dev/gsKit)
- [PCSX2-MCP AI Debugger](https://github.com/hkmodd/PCSX2-MCP)
- [Atlus Typography Article](https://ridwankhan.com/the-typography-of-atlus-usa-35efa4d4220b)
- [Wizardry Fan Translation Wiki](https://wizardry.wiki.gg/wiki/Fan_translation)
- [PS2 Shift-JIS Character Table](https://www.ps2-home.com/forum/viewtopic.php?t=8914)
- [OpenKH TM2 Format Documentation](https://openkh.dev/common/tm2.html)
- [ResHax PS2 4bpp Texture Swizzling](https://reshax.com/topic/696-c-code-to-swizzle-4bpp-ps2-textures/)
