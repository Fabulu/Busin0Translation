# Community Recon: Busin 0 Wizardry Alternative Neo Translation Landscape

Date: 2026-05-28

---

## 1. Has Anyone Else Attempted This Translation?

### Answer: NO full translation patch exists. We are the first.

There is **no existing English patch** for Busin 0: Wizardry Alternative Neo. Multiple community threads confirm this:

- GameFAQs thread ["How is there no patch?"](https://gamefaqs.gamespot.com/boards/918608-busin-0-wizardry-alternative-neo/81041426) - community lamenting the absence
- GameFAQs thread ["Good English translation patch."](https://gamefaqs.gamespot.com/boards/918608-busin-0-wizardry-alternative-neo/81017912) - someone asking about patches, none exist
- The [Wizardry Wiki fan translation page](https://wizardry.wiki.gg/wiki/Fan_translation) lists no Busin 0 patch

### What DOES Exist: Diablo1_reborn's Translation Guide (2021)

The most significant community resource is a **577-page translation guide** (not a patch) created by **Diablo1_reborn** (aka Matrimelee), posted to RPG Codex on April 9, 2021.

- Thread: [Busin 0 Wizardry Alternative Neo (Translation / Guide included)](https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/)
- Format: PDF booklet meant to be read alongside the Japanese game
- Coverage: Full walkthrough with translated dialogue, but missing most item/monster descriptions from the in-game library
- Quality: Author notes grammatical mistakes and spelling errors remain
- Notable: Felipe Pepe (RPG historian) [tweeted about it](https://x.com/felipepepe/status/1386257646165008385), calling it impressive

**This guide is a MAJOR resource for our project** -- it provides translated dialogue text we can cross-reference against our extracted MSG data, and establishes terminology precedent.

---

## 2. Technical Tools and Documentation

### Racjin-Specific Tools

Busin 0 was developed by **Racjin** (also made Naruto games, Bleach Blade Battlers). Key technical resources:

- **[Raw-man/Racjin-de-compression](https://github.com/Raw-man/Racjin-de-compression)** -- GitHub repo with compression/decompression algorithms for Racjin PS2/PSP/Wii games. Handles CFC.DIG and CDDATA.DIG archives. Our game uses PACKDATA.DIG which may follow a similar (but not identical) structure.
- **[SockNastre/CFCDIGCli](https://github.com/SockNastre/CFCDIGCli)** -- Command-line tool for (un)packing Racjin's proprietary CFC.DIG format.
- Romhacking.net thread: ["Find dialogue text in PS2 game (Racjin)"](https://www.romhacking.net/forum/index.php?topic=24817.0) -- Someone (Iredc, 2017) asking about extracting text from a Racjin game. Relevant technical discussion.
- GBAtemp thread: ["RACJIN RAW TEXT FILES DECOMPRESSION"](https://gbatemp.net/threads/racjin-raw-text-files-decompression.614066/) -- Community discussing raw text file formats in Racjin titles.

### General PS2 Translation Resources

- [PS2 Translation Tutorial on Romhacking.net](https://www.romhacking.net/documents/919/) -- General tutorial for PS2 game hacking/translation
- GBAtemp threads on PS2 translation methods: [thread 1](https://gbatemp.net/threads/how-would-i-go-about-translating-a-ps2-game.343902/), [thread 2](https://gbatemp.net/threads/method-for-ps2-language-translations.207932/)

### PCSX2 Compatibility

- [PCSX2 Wiki entry for Busin 0](https://wiki.pcsx2.net/Busin_0:_Wizardry_Alternative_Neo) -- Documents emulator compatibility status

---

## 3. The BUSIN Series Context

### Series Structure

The BUSIN series consists of two PS2 games by Racjin/Atlus:

| Game | Japanese Title | English Title | Released | Localized? |
|------|---------------|---------------|----------|------------|
| BUSIN 1 | BUSIN ~Wizardry Alternative~ | Wizardry: Tale of the Forsaken Land | 2001 | YES (US/EU by Atlus) |
| BUSIN 0 | BUSIN 0 ~Wizardry Alternative Neo~ | (none) | 2003 | Korea only (2005), NO English |

### Relationship Between Games

- **Busin 0 is the PREQUEL**, set ~100 years before Tale of the Forsaken Land
- Both set in the **Kingdom of Duhan** (also spelled "Doohan" in some sources)
- The continent is called **Venoa**
- Directed by **Kouji Okada** (also directed Shin Megami Tensei series)

### Localization Differences in Busin 1 (Tale of the Forsaken Land)

The US localization of Busin 1 made notable changes:
- Removed English voiced narration from opening cutscene
- Added profanity to in-game dialogue (first time in Wizardry series)
- Complete title change from "BUSIN" to "Wizardry: Tale of the Forsaken Land"

**Implication for us**: The US release of Busin 1 establishes official English names for shared lore elements (Kingdom of Duhan, character classes, spell names, etc.) that we should follow for consistency.

---

## 4. Terminology and Naming Consensus

### Races (from guides and wikis)
- Human, Elf, Dwarf, Gnome, Hobbit (standard Wizardry races)
- **Automata** -- new race unique to Busin 0 (automatic dolls, no souls, don't level up, strengthened through item customization)

### Classes (17 total, all attribute/alignment locked)
Fighter, Thief, Mage, Priest, Ninja, Samurai, Bishop, Knight, Alchemist, Monk, Noble Thief, Onmitsu, Shogun, High Thief (and others)

### Key Characters
- **Holy King Ortrud** -- ruler of Duhan, invited adventurers to deal with crisis
- **Bergran von Buren** -- leader of Duhan's Royal Knights
- **Ferry Lefort** -- Lord of Webster, grand chancellor of Duhan
- **Veala** -- Female Human party member
- **Ehrika** -- Female Elf party member
- **Konde** -- Male Human party member
- **Uri Ernst**, **Yoppen Reiner** -- other named characters
- **Aurora** -- the legendary witch whose appearance triggers the game's crisis

### Lore Terms
- **Kingdom of Duhan** (the setting)
- **Karman's Labyrinth** (the dungeon)
- **Battle of Banquo** (historical war, 30 years of conflict)
- **San-Goth** (enemy kingdom whose king was possessed)
- **Spell Stones** -- formed by combining monster parts at the Mage's Tower

### Spell System
Busin 0 uses a unique spell system where you collect monster parts and combine them at the Mage's Tower to create Spell Stones. This differs from traditional Wizardry spell learning. Classic Wizardry spell names (Halito, Katino, Mahalito, etc.) may or may not be used.

---

## 5. Existing English Guides/Walkthroughs

- **GameFAQs Walkthrough by Jerrold** -- [Link](https://gamefaqs.gamespot.com/ps2/918608-busin-0-wizardry-alternative-neo/faqs/27334) -- Covers character creation, races, attributes, classes, spells, monsters, full dungeon walkthrough (B1F-B11F + bonus dungeon)
- **Neoseeker FAQ/Walkthrough v2.0 by JNg** -- [Link](https://www.neoseeker.com/busin0-wizardry/faqs/71897-busin-0.html) -- Comprehensive import guide
- **Diablo1_reborn's 577-page Translation Guide** -- Available via [RPG Codex thread](https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/)
- **YouTube guide by Diablo1_reborn** -- [Link](https://www.youtube.com/watch?v=iQyARMUwuPU)

---

## 6. Other Wizardry Fan Translations (for reference)

| Game | Platform | Status | Translators |
|------|----------|--------|-------------|
| Wizardry: Llylgamyn Saga | PS1/Saturn/PC | Complete (2017) | Community patch |
| Wizardry Chronicle | GBC | Complete | MrRichard999, Helly, Rikoren, et al. |
| Wizardry Empire | GBC | Complete | Community |
| Wizardry Empire II Plus | ? | Complete (2016) | iwakura productions |
| Wizardry Gaiden I | GB | Complete | Community |
| Wizardry Dimguil | PS1 | In progress | RetroGameTalk project |
| **Busin 0** | **PS2** | **No patch exists** | **(This project)** |

---

## 7. Key Takeaways

1. **We are pioneering this translation** -- no one has produced a playable English patch before. The community has been asking for one for years.

2. **Diablo1_reborn's 577-page guide is our best reference** -- it contains translated dialogue and terminology that we should cross-reference. We should obtain this PDF.

3. **Racjin decompression tools exist on GitHub** -- the Raw-man/Racjin-de-compression repo handles Racjin game archives. Our PACKDATA.DIG format may be related to their CFC.DIG/CDDATA.DIG formats.

4. **Tale of the Forsaken Land (Busin 1) establishes official English terminology** -- since it was officially localized by Atlus, we should use its translations for shared lore elements (place names, class names, etc.).

5. **Community interest is high** -- multiple forum threads show people wanting this translation. A release would be well-received.

6. **The Korean localization exists** -- Busin 0 was officially localized in Korean (2005). This might provide insights into how text was modified for localization, though it doesn't directly help with English.

---

## Sources

- [GameFAQs Busin 0 Board](https://gamefaqs.gamespot.com/boards/918608-busin-0-wizardry-alternative-neo/)
- [RPG Codex Translation Guide Thread](https://rpgcodex.net/forums/threads/busin-0-wizardry-alternative-neo-translation-guide-included.138022/)
- [Wizardry Wiki - BUSIN 0](https://wizardry.wiki.gg/wiki/BUSIN_0:_Wizardry_Alternative_NEO)
- [Wizardry Wiki - Fan Translation](https://wizardry.wiki.gg/wiki/Fan_translation)
- [Wizardry Fandom Wiki - BUSIN 0](https://wizardry.fandom.com/wiki/BUSIN_0:_Wizardry_Alternative_NEO)
- [Raw-man/Racjin-de-compression (GitHub)](https://github.com/Raw-man/Racjin-de-compression)
- [SockNastre/CFCDIGCli (GitHub)](https://github.com/SockNastre/CFCDIGCli)
- [Romhacking.net PS2 Translation Tutorial](https://www.romhacking.net/documents/919/)
- [Romhacking.net - Racjin dialogue text thread](https://www.romhacking.net/forum/index.php?topic=24817.0)
- [PCSX2 Wiki - Busin 0](https://wiki.pcsx2.net/Busin_0:_Wizardry_Alternative_Neo)
- [GameFAQs Walkthrough by Jerrold](https://gamefaqs.gamespot.com/ps2/918608-busin-0-wizardry-alternative-neo/faqs/27334)
- [Neoseeker Walkthrough by JNg](https://www.neoseeker.com/busin0-wizardry/faqs/71897-busin-0.html)
- [GBAtemp - Racjin raw text decompression](https://gbatemp.net/threads/racjin-raw-text-files-decompression.614066/)
- [Wikipedia - Wizardry: Tale of the Forsaken Land](https://en.wikipedia.org/wiki/Wizardry:_Tale_of_the_Forsaken_Land)
