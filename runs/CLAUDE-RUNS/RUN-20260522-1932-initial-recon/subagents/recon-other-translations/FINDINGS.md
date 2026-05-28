# PS2 Fan Translation -- Text Reinsertion Research

Date: 2026-05-22

---

## 1. Tales of Destiny 2 PS2: Text Insertion Approach

**Project:** [lifebottle/Tales-of-Destiny-2](https://github.com/lifebottle/Tales-of-Destiny-2) (open-source, Python/Perl/C#)

### Pointer Tables
- Pointer table located in the main ELF executable `SLPS_251.72` starting at offset `0xDD320`.
- Each entry is a 26-bit offset pointing to file offsets inside the ELF.
- PSP variant uses 21-bit offsets + 11-bit flags with sector-based size calculation: `(nextSector - currentSector) * 0x0800 - remainder`.

### Script Format
- Script files use `SCED` signature with two sections:
  - **Code section:** Governs scripted logic, contains pointers to the text section.
  - **Text section:** Strings encoded as font index arrays in a custom format.
- Before compression, files are packed using `SCPK` headers (containing background files, descriptor tables, sprite/animation files, and script files).

### Compression
- PS2 version: mixture of **LZSS + RLE** compression.
- PSP version: **zLib** compression.
- Files must be decompressed before editing, then recompressed for reinsertion.

### Font System
- Uses **TM2 format** (PS2 native texture format) with indexed color palettes.
- 10 four-bit palettes, each 0x40 bytes with 0x10-byte headers.
- Font texture resolution: 128x512 pixels stored as 4-bit data (32,768 bytes).
- Lowercase letter mapping at offset `0x0C9D41` using glyph indices: `0xC9D00 - 0x20 + ASCII_value`.

### Build Pipeline
- Python (71.6%), Perl (20.4%), C# (7.4%).
- External tools: `comptoe.exe` for TM2 conversion.
- Scripts handle bidirectional file extraction/repacking.

**Source:** https://github.com/lifebottle/Tales-of-Destiny-2

---

## 2. Growlanser PS2: Font Replacement

**Project:** [Growlanser VI English Translation](https://growlanser6english.blogspot.com/)

### Font File Handling
- Font stored in `0000002e.fnt` files.
- **Tile Molester** used to export the font table from `.fnt` into `.png`.
- Edited in paint.NET, then reimported back into the `.fnt` file.

### Monospaced vs Variable Width
- GL6 natively supports only **monospaced fonts**.
- When using a proportional font (e.g., Book Antiqua), each character had to be manually stretched/squished to fit the fixed-width cell.

### Variable Width Font (VWF) Implementation
- VWF width table found at offset `0x314C68` inside the game ELF executable.
- Each width value is 1 byte.
- To modify a character's width: add the hex value of the character to `0x314C68`.
- This required assembly-level patching of the ELF to read from the new width table instead of using a constant spacing value.

### General VWF Pattern (Cross-Platform)
1. Find the code point where constant width is added to X-position for next character.
2. Trace back to where width is loaded.
3. Extend the executable to add space for extra code + character width tables.
4. Inject code: when a character is loaded, save a new width by looking up the character in an added width table.

**Source:** https://growlanser6english.blogspot.com/2020/04/gl5-font-has-now-been-implemented-into.html

---

## 3. Common PS2 Translation Tools

### Atlas (Text Insertion)
- **Language:** C++ (Windows executable), latest v1.12 (May 2024).
- **Purpose:** Injects translated text into ROM/game files while maintaining pointer integrity.
- **Features:**
  - Supports custom encodings typical of retro games.
  - Over 45 commands/overloads in its DSL.
  - Three pointer methodologies: embedded pointers, pointer tables, pointer lists.
  - Extensive pointer calculation methods for various ROM architectures.
- **Script format:** Command-based syntax with `#VAR`, `#ADDTBL`, `#CREATEPTR`, `#WRITE`, `<LINE>`, `<END>` tags.
- **Source:** https://github.com/stevemonaco/Atlas

### abcde (Atlas + Cartographer Combined)
- **Language:** Perl (cross-platform; Atlas is Windows-only).
- **Purpose:** Combines Atlas (script insertion) and Cartographer (script dumping) with extra features.
- **Key capabilities:**
  - Dump scripts from game files using pointer tables, or raw text if no pointer table exists.
  - Scripts presented as editable text files.
  - On reinsertion, abcde **automatically recalculates all pointers** to point to new text locations.
  - Can dynamically calculate arbitrary arithmetic values and write them to ROM.
  - Supports pointers whose value is the distance between pointer and text (relative pointers).
  - Can change insert position by relative amount (not just absolute addresses).
  - Can dump multiple strings from a single pointer.
- **Workflow:** Translate text -> comment out Japanese -> run abcde in Atlas mode -> all pointer adjustments handled automatically.
- **Source:** https://www.romhacking.net/utilities/1392/

### Kuriimu
- General-purpose game translation toolkit.
- Plugin architecture (e.g., `file_jmsg` for JMSG format).
- Supports multiple game formats through plugins.
- **Source:** https://www.ps2-home.com/forum/viewtopic.php?t=2965

### Custom Python Scripts
- Most PS2 translation projects end up writing **game-specific tools** in Python.
- Common pattern: Python script to extract -> translate in text files -> Python script to reinsert.
- "99% of the time, you're going to need tools made specifically for the game you want to translate."

### Other Tools Mentioned
- **Tile Molester:** Font/tile graphics editor (export/import `.png`).
- **HxD / hex editors:** For manual inspection and small edits.
- **ELF Modder v1.3:** Modify PS2 ELF headers and code.
- **Cartographer:** Script dumping (predecessor to abcde's dump mode).

---

## 4. Text Overflow Handling (English Longer Than Japanese)

This is a central challenge since English text is almost always longer than Japanese for the same content.

### Strategy 1: Pointer Table Recalculation
- When text grows, update all pointers in the pointer table to reflect new offsets.
- Tools like abcde handle this automatically.
- Atlas also supports automatic pointer recalculation.

### Strategy 2: Exploit 2-Byte vs 1-Byte Encoding
- Japanese often uses 2-byte (Shift-JIS) or multi-byte encoding per character.
- English ASCII uses 1 byte per character.
- Converting from 2-byte Japanese to 1-byte English **doubles available character count** in the same space.
- Example: 100 bytes = 50 Japanese characters OR 100 English characters.

### Strategy 3: Reduce Translation Length
- Abbreviate, use shorter synonyms, trim verbose text.
- This is often the simplest approach for fixed-size fields (item names, menu labels).

### Strategy 4: Relocate Text Data
- Move the text section to unused space in the file or to the end of the file.
- Update pointer table to point to new location.
- Some projects extend the file size to accommodate longer text.

### Strategy 5: Remove Padding/Unused Data
- Many game files have padding bytes (often 0x00 or 0xFF) between sections.
- Reclaim this space for expanded text.

### Strategy 6: Reprogram the Text Engine
- The most complex but most thorough approach.
- Implement VWF to fit more characters in the same pixel width.
- Modify text box dimensions or add scrolling.
- Change font size or use a narrower font.
- Add word-wrapping routines (e.g., Fate/Stay Night Realta Nua PS2 translation wrote a word-wrapping routine in C and injected it into the ELF).

### Strategy 7: Smaller Font Glyphs
- Replace the Japanese font (typically 16x16 or larger) with a smaller English font (e.g., 8x16 or 8x8).
- This effectively doubles horizontal text capacity.

### Real-World Example: Boku no Natsuyasumi 2
- Japanese text displayed vertically; had to be completely reprogrammed to display horizontally.
- Required manual tweaking of: placement, kerning, text color, drop shadow, background, fade in/out, character widths, baselines, character mapping, texture mapping, and spacing.
- All done in low-level MIPS assembly.

---

## 5. Patch Generation (xdelta / BPS)

### xdelta
- **Most common format** for PS2 translation patches.
- Records original size and position of unchanged data, resulting in small patch files.
- Accounts for shifted data so patches don't contain copyrighted content.
- **Command:** `xdelta3 -e -s original.iso modified.iso patch.xdelta`
- **GUI tool:** xdelta UI (frontend for non-command-line users).
- Applied with: `xdelta3 -d -s original.iso patch.xdelta output.iso`

### BPS
- Modern format with better validation and larger modification support.
- Less commonly used for PS2 but gaining popularity.
- Tools: Floating IPS (flips) can create and apply BPS patches.

### PPF (PlayStation Patch Format)
- Historically used for PS1/PS2 disc-based games.
- Simpler format, but less efficient for large changes.

### Workflow for PS2 Patch Distribution
1. Build modified ISO from translated files.
2. Generate xdelta patch: `xdelta3 -e -s original.iso translated.iso patch.xdelta`
3. Distribute only the `.xdelta` file (legal -- contains no copyrighted data).
4. End users apply patch to their own dump of the original game.

### Key Consideration: ISO File Order
- When rebuilding ISOs, **file ordering must be preserved** so that xdelta patches remain small.
- If file positions shift, the delta becomes enormous (potentially gigabytes).
- pycdlib and Ps2IsoTools both support preserving file order for this reason.

---

## 6. PS2 Translation Tutorials and Guides

### romhacking.net PS2 Translation Tutorial
- **URL:** https://www.romhacking.net/documents/919/
- Published December 14, 2023.
- Covers: extracting files from PS2 games, finding text, finding graphics, basic MIPS assembly, finding text routines in PS2 games.
- Created because no comprehensive PS2 translation tutorials previously existed.

### romhacking.net General Text Hacking Tutorial
- **URL:** https://www.romhacking.net/documents/68/
- General-purpose text hacking/translation tutorial (not PS2-specific).

### Forum Discussions
- [romhacking.net forum thread on PS2 Translation Tutorial](https://www.romhacking.net/forum/index.php?topic=38268.0)
- [PCSX2 forum: Making a Translation Patch for PS2](https://forums.pcsx2.net/Thread-Making-a-Translation-Patch-for-PS2)
- [GBAtemp: How to translate PS2 games](https://gbatemp.net/threads/how-can-i-and-what-do-i-need-to-translate-ps2-games.599929/)
- [PS2-HOME forum](https://www.ps2-home.com/forum/viewtopic.php?t=5999)

---

## 7. PS2 ISO Modification Tools

### pycdlib (Python)
- Pure Python library for ISO9660/UDF parsing and creation.
- **Can** work with PS2 ISOs but has limitations:
  - May fail on some PS2 DVD ISOs with UDF CRC errors.
  - Some developers use a "hacky" approach: preserve original headers/metadata, update file sizes/positions, append new data.
  - Resulting ISO may not be 100% UDF-compliant but works on emulators and modded consoles.
- **Key use case:** Preserving file order so xdelta patches can be generated.
- **Source:** https://pypi.org/project/pycdlib/

### Ps2IsoTools (C#)
- Purpose-built for PS2 UDF ISOs.
- Three modes:
  - **UdfReader:** Extract and enumerate files.
  - **UdfEditor:** In-place file replacement (no rebuild needed for simple edits).
  - **UdfBuilder:** Create new ISOs from scratch.
- **Limitation:** Metadata (dates) lost during rebuild; rebuild requires ~2x ISO size in RAM.
- **Source:** https://github.com/Finzenku/Ps2IsoTools

### CDVDGEN 2.0 (Sony Official)
- Official Sony disc-mastering tool.
- Generates proper DVD-ROM (ISO + UDF) images.
- Considered the "gold standard" for PS2 ISO creation.
- Not freely available (part of PS2 SDK).

### UltraISO + CDGenPS2 Workflow
1. UltraISO extracts ISO contents.
2. CDGenPS2 generates an IML file with proper game ID.
3. Import IML back into UltraISO with UDF enabled.
4. Save as standard ISO.

---

## 8. PS2 ELF Executable Modification

### Common Modifications
- **Pointer tables** are often stored in the ELF (main game executable).
- **Font width tables** are typically in the ELF.
- **Text rendering code** (character drawing routines) lives in the ELF.

### Expanding the ELF
- Standard approach: add new data/code sections at the end of the ELF.
- Update ELF headers to reflect new section sizes.
- Tools: ELF Modder, custom scripts.
- ERL (Externally Relocatable Linker) format can be used to create loadable modules.

### Assembly Hacking (MIPS R5900)
- PS2 uses MIPS R5900 (Emotion Engine) processor.
- Text routines typically in MIPS assembly.
- Common modifications:
  - Patch character width loading to use VWF table.
  - Modify text box dimensions.
  - Add word-wrapping logic.
  - Change encoding lookups (Shift-JIS -> ASCII).

---

## 9. Findings Specific to MSG-Format Games

- No widely-used standard "MSG format" tool exists for PS2.
- Each game tends to have its own message/dialogue format.
- Common patterns observed:
  - Header with entry count + offset to text area.
  - Pointer table starting at offset 0x8 with 4-byte pointers.
  - Data area immediately follows pointer table.
  - Text encoded in Shift-JIS (Japanese) or custom encoding tables.
- Custom Python scripts are the norm for game-specific MSG extraction/reinsertion.

---

## 10. Wizardry-Specific Translation History

- Multiple Wizardry titles have been fan-translated (Gaiden I, Llylgamyn Saga, Chronicle, Empire II Plus).
- Most are for older platforms (SNES, PS1, Saturn), not PS2.
- Wizardry: Tale of the Forsaken Land (PS2) already has an official English release.
- No documented open-source tools for PS2 Wizardry text formats were found.
- The text format will likely need to be reverse-engineered from scratch.

**Source:** https://wizardry.wiki.gg/wiki/Fan_translation

---

## Key Takeaways for Our Project

1. **Custom tools are inevitable.** Every PS2 translation project ends up writing game-specific extraction/reinsertion scripts, typically in Python.

2. **Pointer recalculation is critical.** Whether using Atlas/abcde or custom scripts, pointer tables must be updated when text lengths change.

3. **Japanese 2-byte -> English 1-byte gives breathing room.** If the game uses Shift-JIS, switching to ASCII effectively doubles character capacity per byte.

4. **Font replacement requires both graphics and width table work.** Replace the font texture AND update the character width table (in ELF or font file).

5. **VWF is the gold standard** for making English text fit, but requires assembly hacking of the text rendering routine.

6. **ISO rebuilding must preserve file order** to generate reasonable xdelta patches.

7. **xdelta is the standard patch format** for PS2 translations. Generate with `xdelta3 -e -s original.iso modified.iso patch.xdelta`.

8. **pycdlib can work** for ISO modification from Python, but may need workarounds for PS2 UDF quirks. Ps2IsoTools (C#) is a more robust alternative if C# is acceptable.

9. **The romhacking.net PS2 Translation Tutorial** (document #919) is the closest thing to a comprehensive guide and should be studied in detail.

10. **Test early and often in PCSX2.** Most projects iterate between editing files, rebuilding ISO, and testing in emulator.
