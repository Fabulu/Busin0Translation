# Web Research: BUSIN 0 / Wizardry Alternative Neo Translation - Existing Work

Date: 2026-05-22

---

## EXECUTIVE SUMMARY

**No completed English translation patch exists for BUSIN 0: Wizardry Alternative Neo.**

There is a comprehensive 577-page text translation GUIDE (not a patch) by Diablo1_reborn (2021), meant to be read alongside the Japanese game. At least one person on RPG Codex attempted technical hacking work (font renderers, texture atlases) but the project appears stalled/abandoned. A QuickBMS script for PACKDATA.DIG extraction exists but has issues. Several Racjin-specific tools exist on GitHub for related file formats (CFC.DIG, CDDATA.DIG) but none directly handle BUSIN 0's PACKDATA.DIG format.

**Bottom line: The text extraction and font mapping problems for this game remain UNSOLVED. No existing tools can be directly reused, though Racjin-related tools provide a starting point.**

---

## 1. TRANSLATION GUIDE (Text Only - Not a Patch)

- **Author:** Diablo1_reborn (also known as Matrimelee)
- **Released:** April 9, 2021
- **Format:** 577-page PDF/digital booklet
- **Purpose:** Read alongside the Japanese game - NOT a game patch
- **Content:** Full English translation of game text (menus, dialogue, items, etc.)
- **Availability:** RPG Codex thread (linked below)
- **Note from author:** "Patching the game is way beyond [my] capabilities, though everyone is free to use this translation guide for an unofficial translation patch"
- **YouTube video:** https://www.youtube.com/watch?v=iQyARMUwuPU

**This guide is extremely valuable as a translation source** - it means we do NOT need to translate from Japanese. The English text already exists.

### Sources:
- https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/
- https://gamefaqs.gamespot.com/boards/918608-busin-0-wizardry-alternative-neo/79896648
- https://x.com/felipepepe/status/1386257646165008385

---

## 2. TECHNICAL HACKING ATTEMPTS (RPG Codex Thread)

The RPG Codex thread (6+ pages) contains the most relevant technical discussion.

### Key Technical Findings from Thread:
- Someone (username not fully confirmed) attempted a translation patch circa 2021-2022
- They reported getting **font renderers "mostly wrangled"**
- They made progress on translating the **town area**
- The **biggest remaining challenge** was "atlased textures" - textures automatically packed into atlases that need custom packing/unpacking tools
- The patch was updated to support imports from both Japanese and USA ROM versions of the predecessor game (Wizardry: Tale of the Forsaken Land / BUSIN 1)
- The project appears to have **stalled** - no confirmed updates in 2024-2026
- As of April 2024, users were asking for updates with no response

### Thread Pages:
- Page 1: https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/
- Page 2: https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/page-2
- Page 3: https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/page-3
- Page 4: https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/page-4
- Page 6: https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/page-6

**NOTE:** RPG Codex returns HTTP 403 to automated fetchers. These pages need to be reviewed manually in a browser.

---

## 3. PACKDATA.DIG - QuickBMS Script

### Key Discovery: A BMS script exists for BUSIN 0's PACKDATA.DIG

- **Script URL:** http://aluigi.org/bms/busin0_wizardry.bms (also at https://aluigi.altervista.org/quickbms.htm)
- **Tool:** QuickBMS by Luigi Auriemma
- **Status:** Script exists but has reported issues - some users report it doesn't extract all content and crashes at certain files
- **ZenHAX Discussion:** http://zenhax.com/viewtopic.php@t=13890.html
  - Title: "Help With Munge File Packdata.dig Busin 0 Wizardry Alternative Neo"
  - Users tried using CFC.DIG scripts but they don't match PACKDATA.DIG format
  - PACKDATA.DIG is a DIFFERENT format from CFC.DIG/CDDATA.DIG used by other Racjin games

**This is our most important lead** - even if the script is imperfect, it provides a starting point for understanding the PACKDATA.DIG format structure.

**NOTE:** ZenHAX page could not be fetched automatically. Must be reviewed manually.

---

## 4. RACJIN-SPECIFIC TOOLS ON GITHUB

### 4a. Racjin-de-compression (Raw-man)
- **URL:** https://github.com/Raw-man/Racjin-de-compression
- **Language:** C++ with CMake
- **Purpose:** Compression/decompression for Racjin PS2/PSP/Wii games
- **Supported formats:** CFC.DIG and CDDATA.DIG (NOT PACKDATA.DIG)
- **Supported games:** Naruto: Uzumaki Chronicles, Fullmetal Alchemist 3, Bleach: Soul Carnival 2, Naruto Shippuden titles
- **BUSIN support:** NO - does not mention BUSIN or PACKDATA.DIG
- **Status:** Archived since October 2023
- **Relevance:** Medium - same developer (Racjin) but different archive format. Compression algorithms may be similar.

### 4b. CFCDIGCli (SockNastre)
- **URL:** https://github.com/SockNastre/CFCDIGCli
- **Language:** C#
- **Purpose:** Pack/unpack CFC.DIG archives
- **BUSIN support:** NO
- **Status:** Archived since December 2021
- **Relevance:** Low-Medium - CFC.DIG format is different from PACKDATA.DIG

### 4c. RacjinPS2-Scripts (SockNastre)
- **URL:** https://github.com/SockNastre/RacjinPS2-Scripts
- **Language:** Python
- **Purpose:** Extract assets and decode text from decompressed .raw files
- **Key tools:**
  - `raw_unpack.bat` / `unpack_decompressed_raw.py` - Extracts sections from .raw files
  - `raw_text_parse.bat` / `parse_raw_text.py` - Decodes text from .raw files using an encoding table
- **BUSIN support:** NOT SPECIFIED - says "certain Racjin PS2 games" without naming them
- **Status:** Archived, no longer maintained
- **Relevance:** HIGH - the text parsing scripts use an "encoding table for the text encoding used in these games." If BUSIN 0 uses the same Racjin text encoding, these scripts could be directly applicable or easily adapted.

### 4d. GitHub "racjin" Topic
- **URL:** https://github.com/topics/racjin
- **Total repos:** 7 (as of search date)
- **None mention BUSIN or Wizardry**

---

## 5. ROMHACKING.NET

### 5a. "Find dialogue text in PS2 game (Racjin)" Thread
- **URL:** https://www.romhacking.net/forum/index.php?topic=24817.0
- **Content:** Discussion about locating dialogue text in Racjin PS2 games
- **Could not be fetched** - needs manual review
- **Relevance:** Potentially HIGH - may contain format details for Racjin text encoding

### 5b. PS2 Translation Tutorial
- **URL:** https://www.romhacking.net/documents/919/
- **General PS2 translation methodology**

### 5c. No BUSIN entries found
- No translation patches, hacks, or utilities specifically for BUSIN 0 are listed on romhacking.net

---

## 6. GBATEMP

### 6a. "RACJIN RAW TEXT FILES DECOMPRESSION" Thread
- **URL:** https://gbatemp.net/threads/racjin-raw-text-files-decompression.614066/
- **Content:** Discussion about decompressing Racjin raw text files
- **Could not be fetched** - needs manual review
- **Relevance:** HIGH - directly discusses Racjin text file compression

### 6b. No BUSIN-specific threads found on GBATemp

---

## 7. GAMEFAQS DISCUSSIONS

### 7a. "Good English translation patch" Thread
- **URL:** https://gamefaqs.gamespot.com/boards/918608-busin-0-wizardry-alternative-neo/81017912
- **Content:** Users discussing desire for a patch; references the translation guide

### 7b. "How is there no patch?" Thread
- **URL:** https://gamefaqs.gamespot.com/boards/918608-busin-0-wizardry-alternative-neo/81041426
- **Content:** Discussion about technical difficulty of creating a patch
- **Key quote from search results:** Someone "had a hard time due to unfamiliarity with PS2 and how strangely the game is programmed"

### 7c. "There's a translation guide for this game" Thread
- **URL:** https://gamefaqs.gamespot.com/boards/918608-busin-0-wizardry-alternative-neo/79896648
- **Content:** Points users to the Diablo1_reborn translation guide

---

## 8. OTHER RESOURCES

### 8a. Game Wikis
- Wizardry Wiki (wiki.gg): https://wizardry.wiki.gg/wiki/BUSIN_0:_Wizardry_Alternative_NEO
- Wizardry Wiki (Fandom): https://wizardry.fandom.com/wiki/BUSIN_0:_Wizardry_Alternative_NEO
- PCSX2 Wiki: https://wiki.pcsx2.net/Busin_0:_Wizardry_Alternative_Neo

### 8b. GameHacking.org (Cheat Codes)
- https://gamehacking.org/game/96523
- Has cheat codes for the Atlus Best Collection version (NTSC-J)
- May contain useful memory addresses for debugging

### 8c. eXtonix
- No results found for "eXtonix" in connection with BUSIN 0 translation tools
- This person may not have published anything publicly

### 8d. Related Game - Wizardry: Tale of the Forsaken Land (BUSIN 1)
- This predecessor was officially localized in English (released in USA/PAL regions)
- The RPG Codex thread mentions the BUSIN 0 patch supports imports from both JP and USA versions
- Since BUSIN 1 was localized, its English assets could potentially inform font format understanding

---

## 9. KEY TECHNICAL TAKEAWAYS

### What we know about BUSIN 0's data format:
1. **PACKDATA.DIG** is the main archive file (NOT CFC.DIG or CDDATA.DIG used by other Racjin games)
2. A QuickBMS BMS script exists (`busin0_wizardry.bms`) but has extraction issues
3. The game was developed by **Racjin** and published by **Atlus**
4. Font rendering in the game uses **texture atlases** - glyphs are packed into atlas textures
5. Text likely uses a Racjin-proprietary encoding (possibly similar to other Racjin PS2 games)
6. PS2 TIM2 (.tm2) format may be used for textures

### What remains unsolved:
1. Complete, reliable extraction of PACKDATA.DIG contents
2. Identification of text files within the extracted data
3. Understanding of the text encoding / character table
4. Font glyph mapping and atlas layout
5. Reinsertion of modified text back into the archive
6. Rebuilding the ISO with modified data

### Most promising leads to investigate:
1. **Download and test `busin0_wizardry.bms`** - even partial extraction reveals format structure
2. **Review SockNastre's RacjinPS2-Scripts** - the text encoding table may apply to BUSIN 0
3. **Manually read RPG Codex thread pages 2-6** - technical details from the person who worked on font renderers
4. **Manually read ZenHAX thread** - PACKDATA.DIG format discussion
5. **Manually read GBATemp Racjin decompression thread** - compression algorithm details
6. **Manually read romhacking.net Racjin text thread** - text encoding details

---

## 10. PAGES THAT NEED MANUAL BROWSER REVIEW

The following URLs returned 403 errors or were blocked from automated fetching and should be reviewed manually in a web browser:

1. https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/ (all 6 pages)
2. http://zenhax.com/viewtopic.php@t=13890.html (PACKDATA.DIG help thread)
3. https://gbatemp.net/threads/racjin-raw-text-files-decompression.614066/
4. https://www.romhacking.net/forum/index.php?topic=24817.0
5. https://gamefaqs.gamespot.com/boards/918608-busin-0-wizardry-alternative-neo/81041426
6. http://aluigi.org/bms/busin0_wizardry.bms (the actual BMS script to download)
