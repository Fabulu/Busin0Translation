# Recon 07: BUSIN / Wizardry Alternative File Format Research

**Date:** 2026-05-22
**Status:** Partial (web access denied -- findings based on training knowledge + local project analysis)
**Caveat:** WebSearch and WebFetch tools were denied. Findings below are from pre-training knowledge (cutoff May 2025) and analysis of the local project files. URLs should be verified manually.

---

## 1. Existing Romhacking/Translation Work

### BUSIN 0 English Guide (NOT a ROM hack)
- An extensive English gameplay guide (PDF) was created by a user going by **eXtonix**
- Contact: https://steamcommunity.com/id/eXtonix
- RPG Codex thread: https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo.138022/
- Credits mention: **nekobunsin**, **(Harukaze)**, **mauvecow**, **Jerrold NG**
- This is a text guide/walkthrough, NOT a game file translation or ROM hack
- First release: 2021-04-17 (v0.8)

### Known Translation Projects
- **No known complete fan translation patch exists** for BUSIN 0 as of training cutoff (May 2025)
- The original BUSIN / "Wizardry: Tale of the Forsaken Land" was officially localized to English by Atlus USA (2001), so no fan translation was needed for that game
- romhacking.net does not appear to list any translation patches for BUSIN 0 (SLPM-65378)

### Potentially Relevant Community Members
- **nekobunsin** -- credited in the guide; likely a Japanese community member with game knowledge. No known tool releases found in training data
- **mauvecow** -- credited in the guide; known in romhacking circles for PS2 work on other titles. Worth investigating further
- **eXtonix** -- guide author on RPG Codex/Steam; deep game knowledge but appears to be a guide writer, not a ROM hacker

---

## 2. Game File Structure (from local ISO extraction)

The extracted ISO (`SLPM_653.78` = BUSIN 0 JP) contains:

| File | Description |
|------|-------------|
| `SLPM_653.78` | PS2 executable (ELF binary) |
| `SYSTEM.CNF` | PS2 boot configuration |
| `BSN2_0.DSI` | **Main data archive / index** -- likely "BUSIN 2.0 Data System Index" |
| `PACKDATA.DIG` | **Packed game data archive** -- the bulk data container |
| `TEMP1.LZH` | Compressed data (LZH/LZSS compression) |
| `IOPRP254.IMG` | PS2 IOP (I/O Processor) boot image |
| `*.IRX` | PS2 IOP modules (sound, memory card, pad, serial) |
| `MOVIE/` | Directory containing FMV cutscenes (likely PSS/IPU format) |

### Key Files for Translation

1. **PACKDATA.DIG** -- This is almost certainly the main packed data archive containing:
   - Game text / scripts / dialogue
   - Textures (menus, fonts, UI)
   - 3D models
   - Sound effects
   - Map/dungeon data

2. **BSN2_0.DSI** -- Likely the index/directory file for PACKDATA.DIG. The DSI extension may stand for "Data Structure Index." It probably contains:
   - File offsets into PACKDATA.DIG
   - File sizes
   - Possibly file names or type identifiers
   - Compression flags

3. **TEMP1.LZH** -- LZH-compressed data; could be additional assets or a secondary archive

---

## 3. File Format Analysis (Educated Assessment)

### PACKDATA.DIG + DSI Pattern
This is a common PS2 archive pattern: a **flat data blob** (`.DIG`) paired with an **index/directory file** (`.DSI`). The approach:

1. Read the DSI file to get a table of entries (offset, size, possibly name/ID)
2. Use those offsets to extract individual files from the DIG archive
3. Individual files may themselves be compressed (LZH, LZSS, zlib)

### Likely Internal Structure of DSI
Based on similar Racjin/Atlus PS2 games:
- **Header**: Magic bytes, entry count, version info
- **Entry table**: Array of structs, each containing:
  - Offset into PACKDATA.DIG (4 bytes, likely sector-aligned to 2048 bytes)
  - Compressed size (4 bytes)
  - Decompressed size (4 bytes)  
  - File type/ID (2-4 bytes)
  - Possibly compression flag

### Compression
- The presence of `TEMP1.LZH` suggests LZH/LZSS compression is used
- PS2 games from this era commonly used LZSS, LZ77, or custom LZ variants
- Some Atlus PS2 games used a simple LZSS with a 4-byte header (decompressed size) followed by compressed data

### Text Encoding
- Japanese text is almost certainly **Shift-JIS** encoded
- The English localization of the first BUSIN used standard ASCII for English text
- Menu/UI text may be stored as texture images rather than encoded strings (common in PS2 JRPGs)
- Game scripts are likely in a custom bytecode format with embedded Shift-JIS strings

---

## 4. Tools and Resources to Investigate

### QuickBMS
- **No known QuickBMS script specifically for BUSIN/Wizardry Alternative** was found in training data
- QuickBMS scripts for similar Atlus PS2 games may exist on:
  - https://aluigi.altervista.org/quickbms.htm (main QuickBMS site)
  - https://zenhax.com/ (game archive research forum)
  - http://forum.xentax.com/ (file format research, now partially archived)

### Potentially Relevant QuickBMS Scripts
- Search for scripts targeting similar Atlus PS2 titles:
  - Shin Megami Tensei: Nocturne (Atlus, 2003)
  - Digital Devil Saga (Atlus, 2004)
  - Stella Deus (Atlus, 2004)
- These may use similar archive formats if Atlus reused internal tools

### General PS2 Tools
- **PS2 ISO extraction**: Standard ISO9660 tools work (7-zip, PowerISO, etc.)
- **PSS demuxer**: For video files in MOVIE/ directory
- **TIM2 viewer**: PS2 texture format viewer/editor
- **PS2dis**: PS2 ELF disassembler for analyzing the executable

### Hex Analysis Approach
To reverse-engineer the archive format:
1. Open `BSN2_0.DSI` in a hex editor
2. Look for the first 16-32 bytes for a magic signature and entry count
3. Look for repeating patterns (fixed-size structs in the entry table)
4. Cross-reference offset values with the size of `PACKDATA.DIG`
5. Values should be sector-aligned (multiples of 0x800 = 2048)

---

## 5. Atlus PS2 Engine Patterns

### Racjin (Developer) vs Atlus (Publisher)
- **Racjin** developed BUSIN and BUSIN 0, NOT Atlus internally
- Racjin was a smaller studio; their engine is specific to their games, not the broader "Atlus engine"
- Other Racjin PS2 games that might share the engine:
  - **Wizardry: Tale of the Forsaken Land** (same series, same engine)
  - **Naruto: Uzumaki Chronicles** (Racjin, different genre but same studio)
  - **Snowboard Park Tycoon** (Racjin, unlikely to share engine)

### The First BUSIN as Reference
Since "Wizardry: Tale of the Forsaken Land" (BUSIN 1) was released in English:
- Comparing the EN and JP versions of BUSIN 1 would reveal:
  - How text is stored and referenced
  - How the font/character set works
  - Whether text is in scripts or separate data files
  - The text encoding switch from Shift-JIS to ASCII
- The BUSIN 1 English ISO should contain equivalent files (likely `BSN_0.DSI` + `PACKDATA.DIG` or similar)
- **This is the single most valuable resource for understanding the format**

---

## 6. Recommended Next Steps

### Immediate (can do locally)
1. **Hex-dump the DSI file header** -- Identify magic bytes, entry count, struct layout
2. **Hex-dump PACKDATA.DIG header** -- Check for internal magic bytes or if it's purely a data blob
3. **Check TEMP1.LZH** -- Determine if it's standard LZH format or custom
4. **Analyze the ELF executable** -- Search for strings like "PACKDATA", "open", file path references to understand how the game loads data
5. **List MOVIE/ directory** -- Identify video format

### Research (requires web access)
6. **Check romhacking.net** for BUSIN entries:
   - https://www.romhacking.net/ (search for "Wizardry Alternative" or "BUSIN")
7. **Check Xentax/ZenHax forums**:
   - https://zenhax.com/ (search "wizardry ps2" or "PACKDATA")
   - Xentax wiki for PS2 archive formats
8. **Search GitHub** for any BUSIN-related repositories
9. **Check the RPG Codex thread** linked above for any technical discussion
10. **Obtain BUSIN 1 English ISO** for comparative analysis
11. **Contact eXtonix** via Steam to ask about any technical knowledge from guide creation

### Key URLs to Check Manually
- https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo.138022/
- https://steamcommunity.com/id/eXtonix
- https://www.romhacking.net/ (search: "BUSIN", "Wizardry Alternative")
- https://aluigi.altervista.org/quickbms.htm (search for PS2 archive scripts)
- https://zenhax.com/ (search: "wizardry", "PACKDATA", "DSI")
- https://github.com/search?q=busin+wizardry+ps2
- https://gbatemp.net/ (search: "BUSIN 0 translation")

---

## 7. Summary Assessment

**Confidence: Medium-Low** (limited by inability to access web resources)

The BUSIN 0 translation project appears to be **largely unexplored territory**. No known fan translation patch or extraction tools exist specifically for this game as of the training data cutoff. The file format will need to be reverse-engineered, but the approach is straightforward:

1. The DSI+DIG archive pair follows a common PS2 pattern
2. The first game's English release provides an invaluable reference point
3. The archive format is likely simple (index + flat data blob)
4. The main challenges will be: identifying text data within extracted files, understanding the script format, and handling font/character rendering for English text

The guide author (eXtonix) and credited helpers (nekobunsin, mauvecow) may have useful insights but appear to have focused on gameplay documentation rather than ROM hacking.
