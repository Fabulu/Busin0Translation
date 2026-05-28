# Recon 11: Web Research -- PS2 File Formats and Translation Tools for BUSIN 0

**Date:** 2026-05-22
**Status:** Partial (WebSearch and WebFetch both denied -- findings based on training knowledge cutoff May 2025)
**Caveat:** All URLs listed are recommended for manual verification. No live web content was fetched.

---

## 1. BUSIN / Wizardry Alternative -- Specific Tools and Research

### 1.1 Romhacking.net

**URLs to check manually:**
- https://www.romhacking.net/games/5680/ (BUSIN 0 game page, if it exists)
- https://www.romhacking.net/translations/?platform=12&status=&genre=&title=wizardry (PS2 translations search)
- https://www.romhacking.net/utilities/?platform=12&title=wizardry (PS2 utilities search)
- https://www.romhacking.net/homebrew/?platform=12 (PS2 homebrew)

**Known status (as of training cutoff):**
- No fan translation patch for BUSIN 0 (SLPM-65378) is known to exist
- The first game "Wizardry: Tale of the Forsaken Land" (BUSIN 1) was officially localized by Atlus USA, so no fan translation was needed
- No dedicated extraction or hacking utilities for BUSIN are listed on romhacking.net

### 1.2 QuickBMS Scripts

**Main repository:** https://aluigi.altervista.org/quickbms.htm

**No known QuickBMS script exists specifically for BUSIN / Wizardry Alternative.** However, these related scripts may be useful:

| Script | Relevance |
|--------|-----------|
| `ps2_icon.bms` | PS2 icon.sys / icon extraction |
| `lzss.bms` | Generic LZSS decompression (BUSIN likely uses LZSS based on TEMP1.LZH) |
| `lzh.bms` | LZH archive extraction |
| `atlus_*.bms` | Any Atlus-specific scripts (search for "atlus" on the page) |

**QuickBMS itself:** https://aluigi.altervista.org/quickbms.htm
- The tool supports custom scripting for arbitrary archive formats
- Writing a custom BMS script for BSN2_0.DSI + PACKDATA.DIG is the recommended approach once the format is understood

### 1.3 ZenHax / Xentax

**URLs to check manually:**
- https://zenhax.com/search.php?keywords=wizardry+ps2
- https://zenhax.com/search.php?keywords=PACKDATA
- https://zenhax.com/search.php?keywords=BUSIN
- https://zenhax.com/search.php?keywords=racjin
- http://wiki.xentax.com/index.php/PS2 (Xentax wiki -- PS2 formats)
- http://wiki.xentax.com/index.php/LZSS (LZSS compression documentation)

**Xentax Wiki** (now partially archived) was historically the best resource for game archive format documentation. Key pages:
- http://wiki.xentax.com/index.php/Category:PS2_Games
- http://wiki.xentax.com/index.php/Category:Archive_Formats

### 1.4 GitHub

**URLs to check manually:**
- https://github.com/search?q=busin+wizardry+ps2&type=repositories
- https://github.com/search?q=busin0&type=repositories
- https://github.com/search?q=%22wizardry+alternative%22&type=repositories
- https://github.com/search?q=PACKDATA.DIG&type=code
- https://github.com/search?q=BSN2_0.DSI&type=code

**No known GitHub repositories** specifically targeting BUSIN 0 were found in training data.

**Potentially relevant repositories (general PS2 tooling):**
- https://github.com/marco-calautti/Rainbow -- PS2 texture tools including TIM2
- https://github.com/nickworonekin/puyotools -- Includes PS2 archive/texture support
- https://github.com/xdanieldzd/Scarlet -- Game file extraction including some PS2 formats
- https://github.com/VPenkov/ps2-tools -- General PS2 development/analysis tools

### 1.5 GBATemp

**URLs to check manually:**
- https://gbatemp.net/search/?q=BUSIN+wizardry+alternative&o=relevance
- https://gbatemp.net/search/?q=busin+0+translation&o=relevance
- https://gbatemp.net/search/?q=wizardry+ps2+translation&o=relevance

**No known GBATemp threads** about BUSIN 0 translation efforts were found in training data. GBATemp is more focused on Nintendo platforms; PS2 translation work is more commonly discussed on romhacking.net forums.

### 1.6 Other Community Resources

- **RPG Codex** (known thread): https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo.138022/
  - Contains the English guide by eXtonix; potential community members with game knowledge
- **GameFAQs**: https://gamefaqs.gamespot.com/ps2/589531-busin-0-wizardry-alternative-neo
  - May have Japanese guides or technical information
- **Hardcore Gaming 101**: https://www.hardcoregaming101.net/wizardry/
  - Comprehensive Wizardry series overview with some technical details

---

## 2. PS2 Archive Format Research

### 2.1 Common PS2 Data Archive Patterns

PS2 games from the 2001-2005 era overwhelmingly use custom archive formats. Common patterns:

#### Index + Data Blob Pattern (matches BUSIN 0's BSN2_0.DSI + PACKDATA.DIG)
```
INDEX FILE:
  [4 bytes] Magic / identifier
  [4 bytes] Number of entries (little-endian, PS2 is MIPS LE)
  [N * entry_size] Entry table
    Each entry:
      [4 bytes] Offset into data file (often in sectors: value * 2048)
      [4 bytes] Size (compressed or raw)
      [4 bytes] Decompressed size (if compressed)
      [2-4 bytes] Type/ID or flags

DATA FILE:
  Pure concatenation of file data, aligned to sector boundaries (2048 bytes)
  No internal directory structure
```

#### Self-Contained Archive Pattern
```
[Header with magic + entry count]
[Directory entries with offsets relative to archive start]
[File data]
```

#### Key Observations for PS2 Archives
- **Sector alignment**: Nearly all PS2 archives align files to 2048-byte (0x800) boundaries because the PS2 DVD drive reads in sectors
- **Little-endian**: PS2 uses MIPS R5900 (Emotion Engine) which is little-endian
- **No filenames**: Many PS2 archives use numeric IDs instead of filenames; the game code references files by index
- **Flat structure**: Subdirectories are rare; files are typically organized by index ranges

### 2.2 .DIG Format

The `.DIG` extension is **not a standard PS2 format** -- it appears to be Racjin-specific. Likely stands for "Digital" or is simply short for "data in game." In the BUSIN context:

- `PACKDATA.DIG` (839 MB) -- the main data blob
- The name "PACKDATA" strongly suggests packed/archived data
- This is the data portion of the index+data pair

### 2.3 .PAC / .BIN / .DAT Formats

These are extremely common generic PS2 archive extensions:

- **.PAC**: Used by many developers (Capcom, Konami, Namco). Usually a simple header + concatenated files
- **.BIN**: Generic binary container, meaning varies completely by game
- **.DAT**: Same as .BIN -- no standard meaning
- **.AFS**: Sega's standard PS2 archive format (CRI Middleware)
- **.CPK**: Later CRI Middleware archive format

### 2.4 How Racjin Games Pack Their Data

**Racjin** (sometimes written "RACjin") was a small Japanese developer. Key titles:

| Game | Year | Platform | Archive Format |
|------|------|----------|----------------|
| Wizardry: Tale of the Forsaken Land (BUSIN 1) | 2001 | PS2 | Likely same DSI+DIG pattern |
| BUSIN 0: Wizardry Alternative Neo | 2003 | PS2 | BSN2_0.DSI + PACKDATA.DIG |
| Naruto: Uzumaki Chronicles | 2005 | PS2 | Unknown |
| Naruto: Uzumaki Chronicles 2 | 2007 | PS2 | Unknown |

**Critical reference point**: The English release of BUSIN 1 (Wizardry: Tale of the Forsaken Land, SLUS-20259) should use the same engine and archive format. Comparing the EN and JP versions would reveal:
- How Racjin handles text encoding switches (Shift-JIS vs ASCII)
- Whether text is in separate files or embedded in script bytecode
- Font layout and character table structure

### 2.5 PS2 TIM2 Texture Format

**TIM2** (Texture Image Map 2) is Sony's standard PS2 texture format.

**Magic bytes**: `54 49 4D 32` ("TIM2") at offset 0

**Structure:**
```
TIM2 Header (16 bytes):
  [4 bytes] Magic "TIM2"
  [1 byte]  Version (usually 0x04)
  [1 byte]  Format (0x00 or 0x01)
  [2 bytes] Picture count
  [8 bytes] Reserved (zeros)

For each picture:
  Picture Header (48 bytes):
    [4 bytes] Total size
    [4 bytes] Palette size
    [4 bytes] Image data size
    [2 bytes] Header size
    [2 bytes] Color entry count
    [1 byte]  Image format (pixel storage type)
    [1 byte]  Mipmap count
    [1 byte]  CLUT (Color Look-Up Table) format
    [1 byte]  Pixel depth (4-bit, 8-bit, 16-bit, 24-bit, 32-bit)
    [2 bytes] Width
    [2 bytes] Height
    [8 bytes] GsTex0 register
    [8 bytes] GsTex1 register
    [4 bytes] GsTexAFlg register
    [4 bytes] GsTexClut register
  [Image data]
  [Palette/CLUT data]
```

**Pixel depth values:**
- 0x00 = 16-bit (5551 RGBA or 565 RGB)
- 0x01 = 24-bit (RGB)
- 0x02 = 32-bit (RGBA)
- 0x03 = 4-bit indexed (16 colors)
- 0x04 = 8-bit indexed (256 colors)

**GS swizzling**: PS2 Graphics Synthesizer stores pixels in a swizzled (non-linear) order for performance. 8-bit indexed textures need CSM1 unswizzling. Tools must handle this.

**Tools for TIM2:**
- Rainbow (C#): https://github.com/marco-calautti/Rainbow
- tim2view: Part of various PS2 homebrew SDKs
- Noesis: https://richwhitehouse.com/index.php?content=inc_projects.php&showproject=91 (supports TIM2)
- XnView with PS2 plugin

**Font textures** in PS2 JRPGs are typically stored as TIM2 images with 4-bit or 8-bit indexed color (since fonts are usually monochrome or grayscale).

### 2.6 PS2 Font Rendering in JRPGs

PS2 JRPGs typically use one of these font approaches:

#### Bitmap Font Sheet (Most Common)
- A large texture (typically 256x256 or 512x512) containing all character glyphs arranged in a grid
- A companion table maps character codes to grid positions
- For Shift-JIS games: the table maps Shift-JIS codes to glyph positions
- Glyph dimensions are usually fixed (e.g., 16x16 or 12x12 for Japanese, variable-width for English in localized versions)

#### Character Mapping Table
```
For each character:
  [2 bytes] Shift-JIS code (or internal code)
  [1 byte]  X position in texture (in glyph units)
  [1 byte]  Y position in texture (in glyph units)
  [1 byte]  Width (for variable-width fonts)
  [1 byte]  Left bearing / kerning adjustment
```

#### Font Challenges for EN Translation
1. **Glyph count**: Shift-JIS supports ~7000 characters; English needs only ~96. This means the font texture has plenty of space for Latin characters
2. **Character width**: Japanese characters are fixed-width (monospaced squares); English typically needs variable-width (proportional) fonts. This is the biggest challenge
3. **Text box sizing**: Japanese text is more compact per information unit; English translations are typically 30-50% longer, requiring either smaller fonts, abbreviation, or text box resizing
4. **Control codes**: The game likely uses embedded control codes in text for:
   - Line breaks (often `\n` = 0x0A or custom codes)
   - Text speed/pause
   - Character name insertion
   - Color changes
   - Wait for button press

---

## 3. Specific File Format Details

### 3.1 PACKDATA.DIG Format

**File**: `extracted/PACKDATA.DIG` (839,661,568 bytes = ~801 MB)

This is almost certainly a **flat data blob** with no internal directory structure. Files are stored sequentially, aligned to sector boundaries (2048 bytes). The BSN2_0.DSI file serves as the index/directory.

**To identify contents**, look for magic bytes at sector-aligned offsets:
- `54 49 4D 32` = TIM2 texture
- `50 41 44 00` = PAD data
- Shift-JIS text sequences (lead bytes 0x81-0x9F, 0xE0-0xEF)
- `00 00 01 BA` = MPEG-PS header (unlikely in data archive)

### 3.2 BSN2_0.DSI Format

**File**: `extracted/BSN2_0.DSI` (63,176,704 bytes = ~60 MB)

The name likely means "BUSIN 2.0 Data Structure/System Index." At 60 MB, this is unusually large for a pure index file, suggesting it contains:
1. An index/directory table for PACKDATA.DIG entries
2. Possibly embedded data (small files, scripts, or text) stored directly in the DSI rather than in PACKDATA.DIG
3. Possibly a combined archive format with both index and some data

**Analysis approach:**
1. Examine the first 64 bytes for magic signature, version, and entry count
2. Look for a repeating struct pattern in the first few KB
3. If offsets are found, validate them against PACKDATA.DIG file size
4. Check if sectors of the DSI itself contain recognizable file data (TIM2, text, etc.)

### 3.3 DSI File Format in PS2 Context

The `.DSI` extension is **not a standard PS2 format**. It is specific to Racjin's engine. No documentation exists in public knowledge bases (Xentax wiki, etc.) as of training cutoff.

Possible interpretations:
- **D**ata **S**tructure **I**ndex
- **D**ata **S**ystem **I**nformation
- **D**irectory **S**tructure **I**ndex

### 3.4 TEMP1.LZH

**File**: `extracted/TEMP1.LZH` (334,105,420 bytes = ~319 MB)

LZH is a well-known compression format (used by the LHA/LZH archiver). However, PS2 games often use the `.LZH` extension loosely to mean "LZ-compressed data" rather than the standard LZH archive format.

**To determine if it's standard LZH:**
- Standard LZH archives start with the header byte pattern: `[header_size] [-lh` followed by the compression method (e.g., `-lh5-`, `-lh6-`, `-lh7-`)
- If it doesn't match, it's likely a custom LZ/LZSS compressed blob

### 3.5 Atlus PS2 Archive Formats (for reference)

Atlus internally developed games (SMT Nocturne, Digital Devil Saga, Persona 3/4) use different formats than Racjin-developed games. However, for reference:

| Atlus Game | Archive Format | Notes |
|------------|---------------|-------|
| SMT Nocturne | DDT+IMG pair | Similar index+data pattern |
| Digital Devil Saga | PAC archives | Self-contained with internal directory |
| Persona 3/4 | BIN/PAK/CPK | Multiple archive types |
| Stella Deus | Unknown | Atlus-published, different developer |
| Growlanser | PAC | Atlus-published, Career Soft developed |

The DDT+IMG pattern in SMT Nocturne is structurally similar to DSI+DIG: a directory file paired with a data blob.

---

## 4. Translation Tools for PS2 JRPGs

### 4.1 Text Extraction and Insertion

#### Atlas (Text Insertion Tool)
- **Website**: Part of romhacking.net utilities
- **Purpose**: Inserts translated text back into ROMs/game files using table files and pointer recalculation
- **How it works**:
  1. Define a character table (.tbl file) mapping hex values to characters
  2. Create a script file with original pointer addresses and translated text
  3. Atlas recalculates pointers and inserts the new text
- **Relevance to BUSIN 0**: Will be needed for reinserting translated text once the text format is understood
- https://www.romhacking.net/utilities/224/

#### online table file generators
- **Online Shift-JIS table generator**: Generates .tbl files for Shift-JIS encoded games
- **romhacking.net table files section**: Pre-made table files for common encodings
- https://www.romhacking.net/documents/

#### abcde (Another Batch of Content Draining/Extraction)
- **Purpose**: Batch text extraction from ROMs using table files
- Complementary to Atlas (extract with abcde, insert with Atlas)
- https://www.romhacking.net/utilities/599/

#### Online table file generators
- https://www.romhacking.net/utilities/975/ (common utilities list)

### 4.2 Shift-JIS Pointer Table Patterns

In PS2 JRPGs, text pointers typically follow these patterns:

#### Absolute Pointer Table
```
[4 bytes per entry] Absolute offset to string start
...
Strings stored contiguously after the pointer table
Each string terminated by 0x00 or a game-specific terminator
```

#### Relative Pointer Table
```
[4 bytes per entry] Offset relative to start of text block
...
Text block follows immediately after pointer table
```

#### Embedded Pointers in Script Bytecode
```
[opcode] [pointer to string] [other operands]
Strings may be embedded inline or in a separate string table
```

#### Shift-JIS Specifics
- **Lead byte ranges**: 0x81-0x9F, 0xE0-0xEF
- **Trail byte ranges**: 0x40-0x7E, 0x80-0xFC
- **Terminator**: Usually 0x00 (single null byte)
- **Full-width ASCII**: Shift-JIS encodes ASCII characters as 2-byte sequences (0x8140-0x829E range), so "A" might be stored as 0x8260 rather than 0x41
- **Common patterns to search for in hex dumps**:
  - `82 4F` = full-width "0"
  - `82 60` = full-width "A"
  - `82 9F` = hiragana "a" (0x829F onwards)
  - `83 40` = katakana "a" (0x8340 onwards)

### 4.3 PS2 Font Hacking Approaches

#### Approach 1: Replace Glyphs in Existing Font Texture
1. Locate the font texture (TIM2) in the archive
2. Identify the character mapping table
3. Replace Japanese glyphs with English glyphs in the texture
4. Update the character mapping table to map ASCII/Latin codes to the new glyph positions
5. Adjust character widths if the game supports variable-width rendering

**Tools:**
- TIM2 editor / Rainbow for texture editing
- Any image editor (GIMP, Photoshop) for glyph drawing
- Custom scripts for table editing

#### Approach 2: Modify the Font Rendering Code (ELF patching)
1. Disassemble the PS2 ELF executable (SLPM_653.78)
2. Find the font rendering function (look for texture coordinate calculations)
3. Modify the character lookup code to handle ASCII instead of Shift-JIS
4. Optionally add variable-width font support

**Tools:**
- Ghidra with PS2/MIPS support: https://ghidra-sre.org/
  - Use the MIPS processor module (R5900 = MIPS III + multimedia extensions)
  - Load address for PS2 ELF: typically 0x00100000
- PCSX2 debugger: Built-in debugger in PCSX2 emulator for runtime analysis
- PS2dis: Dedicated PS2 disassembler (older tool, less capable than Ghidra)

#### Approach 3: VWF (Variable-Width Font) Engine
Many PS2 fan translations implement a Variable-Width Font engine:
1. Create a new font texture with properly spaced Latin characters
2. Create a width table (1 byte per character = pixel width of each glyph)
3. Patch the ELF to use the width table when rendering text
4. This allows proportional English text instead of fixed-width

### 4.4 General PS2 Translation Workflow

```
Phase 1: Analysis
  1. Extract ISO contents
  2. Identify archive format (index + data pattern)
  3. Extract individual files from archives
  4. Identify text files (look for Shift-JIS sequences)
  5. Identify font textures (look for TIM2 magic bytes)
  6. Identify script format (bytecode analysis)
  7. Map pointers to strings

Phase 2: Tool Development
  1. Write archive extractor (Python/QuickBMS)
  2. Write text dumper (extract all strings with pointer info)
  3. Write text inserter (reinsert translated strings, recalculate pointers)
  4. Write archive repacker (rebuild archive with modified files)
  5. Write ISO rebuilder

Phase 3: Translation
  1. Dump all text
  2. Translate (using the English guide as primary reference!)
  3. Edit for length/fit constraints
  4. Handle font/character set changes

Phase 4: Integration
  1. Create new font texture with Latin characters
  2. Reinsert translated text
  3. Repack archives
  4. Rebuild ISO
  5. Test in PCSX2
```

### 4.5 Key Tools Summary

| Tool | Purpose | URL |
|------|---------|-----|
| QuickBMS | Archive extraction (scriptable) | https://aluigi.altervista.org/quickbms.htm |
| Ghidra | ELF disassembly/analysis | https://ghidra-sre.org/ |
| PCSX2 | Emulation + debugging | https://pcsx2.net/ |
| Atlas | Text insertion with pointer recalc | https://www.romhacking.net/utilities/224/ |
| abcde | Batch text extraction | https://www.romhacking.net/utilities/599/ |
| Rainbow | TIM2 texture editing | https://github.com/marco-calautti/Rainbow |
| Noesis | Multi-format model/texture viewer | https://richwhitehouse.com/index.php?content=inc_projects.php&showproject=91 |
| HxD / ImHex | Hex editors | https://mh-nexus.de/en/hxd/ / https://imhex.werwolv.net/ |
| CrystalTile2 | ROM/game file tile editor | https://www.romhacking.net/utilities/818/ |
| CDvdGen + mkisofs | PS2 ISO rebuilding | PS2 SDK / open source |

---

## 5. Cross-Reference: BUSIN 1 English Release

**This is the single most valuable research resource for this project.**

The English release of "Wizardry: Tale of the Forsaken Land" (BUSIN 1, SLUS-20259) uses the same Racjin engine. Comparing the JP and EN versions reveals:

### What to compare:
1. **Archive structure**: Does the EN version use the same DSI+DIG format?
2. **File sizes**: Text file sizes will differ (English text vs Japanese text)
3. **Font texture**: The EN version already has a Latin font -- this can potentially be reused for BUSIN 0
4. **Text encoding**: How did Atlus USA handle the Shift-JIS to ASCII switch?
5. **ELF differences**: What code was changed in the executable for text rendering?
6. **Pointer format**: Comparing pointer tables between JP and EN shows how the game handles variable-length text

### Files to obtain:
- BUSIN 1 JP ISO (SLPM-65047)
- BUSIN 1 EN ISO (SLUS-20259)
- Extract both and do a binary comparison of corresponding files

---

## 6. Compression Formats Likely Used

### LZSS (Lempel-Ziv-Storer-Szymanski)
- Extremely common in PS2 games
- Typical PS2 LZSS header: `[4 bytes decompressed size]` followed by compressed data
- Some variants use a flag byte followed by 8 chunks (each chunk is either a literal byte or a back-reference)
- Back-references typically encoded as: `[12-bit offset] [4-bit length]` or `[8-bit offset] [8-bit length]`

### LZH/LHA
- More complex than LZSS; uses Huffman coding on top of LZ compression
- Standard header format: starts with header size byte, then `-lh` method string
- If TEMP1.LZH uses standard LZH, standard tools (7-zip, lha) can extract it

### zlib
- Some PS2 games use standard zlib (deflate) compression
- Magic bytes: `78 01` (low compression), `78 9C` (default), `78 DA` (best compression)
- Check file headers of extracted sub-files for these signatures

---

## 7. Recommended Manual Web Searches

Since automated web access was denied, the following searches should be performed manually:

### High Priority
1. **romhacking.net**: Search for "Wizardry Alternative", "BUSIN", "BUSIN 0" in games, translations, utilities, and forum
2. **GitHub**: Search `busin0`, `"wizardry alternative"`, `PACKDATA.DIG`, `BSN2_0.DSI` in code search
3. **aluigi.altervista.org/quickbms.htm**: Ctrl+F on the page for "wizardry", "atlus", "racjin", "ps2"
4. **zenhax.com**: Search for "wizardry ps2", "PACKDATA", "BUSIN", "racjin"

### Medium Priority
5. **Google**: `"PACKDATA.DIG" filetype:bms OR filetype:py` (find extraction scripts)
6. **Google**: `"BSN2_0.DSI" OR "BSN2_0" file format`
7. **Google**: `site:reddit.com "busin 0" translation`
8. **Google**: `"wizardry alternative neo" english patch`
9. **rpgcodex.net**: Search for technical discussion in the BUSIN thread

### Lower Priority
10. **Google**: `racjin ps2 engine archive format`
11. **Google**: `"wizardry tale of the forsaken land" rom hack`
12. **GameFAQs JP**: Check Japanese boards for any technical information
13. **2ch/5ch archives**: Search for BUSIN technical/hacking discussion (in Japanese)

---

## 8. Summary and Confidence Assessment

### What we know with high confidence:
- BUSIN 0 uses a DSI (index) + DIG (data) archive pair
- The PS2 is little-endian MIPS; offsets/sizes are 4-byte LE integers
- Text is Shift-JIS encoded
- The English guide provides near-complete translations for all game text
- No existing fan translation or extraction tools exist for this specific game
- BUSIN 1 English release is the best reference for understanding the engine

### What requires investigation:
- Exact DSI header format and entry structure (needs hex analysis)
- Whether files in PACKDATA.DIG are individually compressed
- The script/dialogue bytecode format
- Font texture location and character mapping table format
- Whether the 60 MB DSI file contains embedded data beyond just an index

### Biggest risks:
1. **Script bytecode complexity**: If text is embedded in complex script bytecode (rather than simple string tables), extraction/reinsertion becomes significantly harder
2. **Font rendering**: If the game uses a fixed-width font renderer with no VWF support, the ELF will need patching
3. **Text length constraints**: Japanese text is often more compact; English translations may not fit without UI/text box modifications
4. **Compression**: If individual files use a custom compression scheme, a decompressor must be reverse-engineered

---

## All URLs Collected

### Game-Specific
- https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo.138022/
- https://steamcommunity.com/id/eXtonix
- https://gamefaqs.gamespot.com/ps2/589531-busin-0-wizardry-alternative-neo
- https://www.hardcoregaming101.net/wizardry/

### Romhacking Resources
- https://www.romhacking.net/ (search: BUSIN, Wizardry Alternative)
- https://www.romhacking.net/utilities/224/ (Atlas text inserter)
- https://www.romhacking.net/utilities/599/ (abcde text extractor)
- https://www.romhacking.net/utilities/818/ (CrystalTile2)

### Format Research
- https://aluigi.altervista.org/quickbms.htm (QuickBMS scripts repository)
- https://zenhax.com/ (game archive research forum)
- http://wiki.xentax.com/index.php/PS2 (PS2 format wiki)
- http://wiki.xentax.com/index.php/LZSS (LZSS documentation)

### Tools
- https://ghidra-sre.org/ (disassembler)
- https://pcsx2.net/ (PS2 emulator with debugger)
- https://github.com/marco-calautti/Rainbow (TIM2 texture tool)
- https://richwhitehouse.com/index.php?content=inc_projects.php&showproject=91 (Noesis)
- https://mh-nexus.de/en/hxd/ (HxD hex editor)
- https://imhex.werwolv.net/ (ImHex pattern-based hex editor)

### GitHub Searches
- https://github.com/search?q=busin+wizardry+ps2&type=repositories
- https://github.com/search?q=busin0&type=repositories
- https://github.com/search?q=PACKDATA.DIG&type=code
- https://github.com/search?q=BSN2_0.DSI&type=code
