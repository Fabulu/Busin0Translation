# BUSIN 0 Community Research Findings

**Date:** 2026-05-22
**Status:** INCOMPLETE -- WebSearch, WebFetch, and Bash (curl) were all permission-denied. Findings below are from training-data knowledge only and MUST be verified with live web access.

---

## 1. RPG Codex Thread

**URL:** https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo.138022/

**Status:** Could not fetch. Needs manual review.

**What to look for:** Any posts discussing file formats, ISO layout, text encoding (Shift-JIS), or modding feasibility. RPG Codex has a strong niche community for obscure JRPGs and someone may have discussed extraction.

---

## 2. eXtonix (Guide Author)

**URL:** https://steamcommunity.com/id/eXtonix

**Training-data knowledge:**
- eXtonix authored a detailed English guide/FAQ for BUSIN 0 (Wizardry Alternative Neo) available on GameFAQs.
- The guide contains extensive gameplay information including item lists, spell lists, class data, and quest walkthroughs -- all of which had to be manually translated/cross-referenced from the Japanese game.
- No evidence from training data that eXtonix created extraction tools or text dumps. The guide appears to have been written through manual play and cross-referencing Japanese wikis.
- The Steam profile may link to other resources.

**Action items:**
- Check if eXtonix has a GitHub or other code repositories
- Contact via Steam if translation collaboration is desired

---

## 3. nekobunsin and mauvecow

**Training-data knowledge:**

### mauvecow
- mauvecow is a known romhacker with credits on several translation projects
- Has worked on PS1/PS2 era games
- Check https://www.romhacking.net/ credits and personal site
- May have technical knowledge about PS2 game text formats

### nekobunsin
- Less well-known; may have contributed to the guide or community knowledge
- Search romhacking.net and GameFAQs for contributions

**Action items:**
- Search romhacking.net contributor databases for both names
- Check GitHub for any repositories from either contributor
- Look for mauvecow's personal site/blog which may document PS2 hacking techniques

---

## 4. GameFAQs / Forums

**URLs to check:**
- https://gamefaqs.gamespot.com/ps2/589553-busin-0-wizardry-alternative-neo
- https://gamefaqs.gamespot.com/ps2/589553-busin-0-wizardry-alternative-neo/faqs

**Training-data knowledge:**
- GameFAQs has the eXtonix guide listed for BUSIN 0
- The game's message board may have scattered translation discussion
- BUSIN 0 is a relatively obscure title even among Wizardry fans, so forum activity is likely minimal

---

## 5. Romhacking.net

**URLs to check:**
- https://www.romhacking.net/ (search for: BUSIN, SLPM-65378, Wizardry Alternative Neo)
- https://www.romhacking.net/?page=utilities&platform=2 (PS2 utilities)
- https://www.romhacking.net/?page=translations&platform=2 (PS2 translations)

**Training-data knowledge:**
- As of training cutoff, NO completed or in-progress translation patch for BUSIN 0 is listed on romhacking.net
- PS2 translation projects on romhacking.net are relatively rare due to the complexity of PS2 game formats
- General PS2 text tools that may be useful:
  - **Analysis tools:** PS2dis (PS2 disassembler), generic ISO extractors
  - **Text tools:** Generic Shift-JIS table editors, common PS2 text formats vary heavily per developer

**Note about SLPM-65378:** This is the game's serial number. Searching for it may turn up technical databases (redump.org, etc.) with disc structure info.

---

## 6. Existing Partial Translations / Text Dumps

**Training-data knowledge:**
- NO known public translation patch or text dump for BUSIN 0 exists as of training cutoff
- This appears to be essentially virgin territory for fan translation
- The eXtonix guide represents the most comprehensive English-language documentation of the game's content but is not a text extraction

---

## 7. BUSIN 1 / Tale of the Forsaken Land Comparison

**Training-data knowledge:**

### Key facts about Tale of the Forsaken Land (BUSIN 1)
- **JP title:** BUSIN: Wizardry Alternative (SLPM-65048)
- **EN title:** Wizardry: Tale of the Forsaken Land (SLUS-20259)
- **Developer:** Racjin (same developer as BUSIN 0)
- **Publisher:** Atlus (NA release)
- Both games were developed by the same studio (Racjin), so they very likely share engine architecture and file formats

### What the official EN release reveals
- Since Tale of the Forsaken Land received an official English localization, comparing the JP and EN ISOs could be extremely valuable:
  - **File structure comparison:** diff the ISO contents to see which files changed (text files will differ, graphics with embedded text will differ)
  - **Text encoding:** The EN version likely uses ASCII/extended ASCII where the JP version uses Shift-JIS. Finding corresponding files reveals the text format.
  - **Font files:** The EN version needed Latin character fonts. Identifying these files in BUSIN 1 EN helps locate equivalent files in BUSIN 0.
  - **Executable comparison:** Comparing SLUS-20259.ELF with SLPM-65048.ELF may reveal text rendering routines and encoding tables.

### Recommended approach
1. Obtain both JP and EN ISOs of BUSIN 1 (Tale of the Forsaken Land)
2. Extract and diff file listings -- identify which files differ
3. Binary-diff corresponding files to identify text storage format
4. Apply discovered format knowledge to BUSIN 0 files (which likely use the same or very similar format since same engine/developer)

**This is likely the single most productive shortcut available.** The official EN localization of the predecessor game on the same engine is a Rosetta Stone.

---

## Summary of Actionable Next Steps

| Priority | Task | Notes |
|----------|------|-------|
| HIGH | Compare BUSIN 1 JP vs EN ISOs | Same engine = same formats. This is the fastest path to understanding text storage. |
| HIGH | Manually visit RPG Codex thread | May contain technical discussion we couldn't fetch |
| MEDIUM | Search romhacking.net with live access | Verify no tools/patches exist |
| MEDIUM | Search GitHub for mauvecow repositories | Known romhacker, may have relevant tools |
| LOW | Contact eXtonix | Guide author, deep game knowledge but likely no technical tools |
| LOW | Search for Racjin engine documentation | Other Racjin games may have been hacked, revealing shared engine details |

---

## Other Racjin PS2 Games (Same Engine Potential)

Racjin developed several PS2 titles. If any have been hacked/translated, their tools may apply:
- Shining Force Neo (2005)
- Shining Force EXA (2007)
- Fullmetal Alchemist games
- Naruto: Uzumaki Chronicles series

Check romhacking.net for any Racjin game tools/translations.

---

## IMPORTANT CAVEAT

**This document was generated WITHOUT live web access.** All information is from training data (cutoff ~May 2025). A follow-up run with WebSearch/WebFetch permissions enabled is needed to:
1. Actually fetch and read the RPG Codex thread
2. Check eXtonix's current Steam profile and linked resources
3. Search romhacking.net's current database
4. Find any post-2024 developments in the community
