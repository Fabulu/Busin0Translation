# Capitalization Fix Summary

Date: 2026-05-28

## Problem
Translation entries used inconsistent casing. The original chunk translations (r38 races, classes, stats) used Title Case ("Human", "Elf", "HP", "STR"), but fix files and later translations used lowercase ("samurai ring", "mage soul", "bubbly slime").

## Files Modified

### 1. chunk_r34_fix.json -- 563 entries fixed
All item names converted from lowercase to Title Case:
- Equipment: "samurai ring" -> "Samurai Ring", "leather armor" -> "Leather Armor"
- Weapons: "excalibur" -> "Excalibur", "crystal sword" -> "Crystal Sword"
- Consumables: "healing potion" -> "Healing Potion", "mage soul" -> "Mage Soul"
- Scrolls: "scroll of kureta" -> "Scroll of Kureta"
- Materials: "dragon scale" -> "Dragon Scale", "spider thread" -> "Spider Thread"
- Key items: "golden key" -> "Golden Key", "princess brooch" -> "Princess Brooch"
- Categories: "short sword" -> "Short Sword", "hand axe" -> "Hand Axe"
- Unidentified: "?ring" -> "?Ring", "?armor" -> "?Armor"

### 2. chunk_r36_translated.json -- 158 entries fixed
All monster/NPC names converted to Title Case:
- "bubbly slime" -> "Bubbly Slime"
- "gas dragon" -> "Gas Dragon"
- "undead kobold" -> "Undead Kobold"

### 3. chunk_r37_extra.json -- 2 entries fixed
- "kana" -> "Kana"
- "sym" -> "Sym"

### 4. chunk_r37_r48_r49_translated.json -- 225 entries fixed
- r37 UI labels: "bonus point" -> "Bonus Point", "abc" -> "ABC", "ok" -> "OK"
- r48 shop names (107 entries): "illegal dump site" -> "Illegal Dump Site", "general store" -> "General Store"
- r49 trap names: "spear" -> "Spear", "poison gas" -> "Poison Gas", "MP Drain"
- r49 floor labels: "floor above" -> "Floor Above", "yes" -> "Yes", "cancel" -> "Cancel"
- r49 dialogue: capitalized first letter of sentences

### 5. chunk_r40_r42_translated.json -- 69 entries fixed
- r40 menu options: "status" -> "Status", "change class" -> "Change Class", "add to party" -> "Add to Party"
- r40 sort options: "party order" -> "Party Order", "alphabetical" -> "Alphabetical"
- r40 NPC names: "hina" -> "Hina", "ricardo" -> "Ricardo"
- r41 labels: "yes" -> "Yes", "no" -> "No", "not enough gold" -> "Not Enough Gold"
- r42 labels: "yes" -> "Yes", "has awakened" -> "Has Awakened"
- All dialogue: capitalized first letter of sentences

### 6. chunk_r43_r45_translated.json -- 32 entries fixed
- r44 stat labels: "mhp" -> "MHP", "str" -> "STR" (ALL CAPS to match r38)
- r44 labels: "up" -> "Up", "pt" -> "Pt"
- r45 branch names: "b1 branch" -> "B1 Branch"
- r45 floor labels: "b1f" -> "B1F" (uppercase F)
- r45: "days" -> "Days", "received!" -> "Received!"

### 7. chunk_01_translated.json -- 18 entries fixed
- r36 enemy descriptions: "lv3 Priest" -> "Lv3 Priest" (15 entries)
- r37 prompts: "enter your name." -> "Enter Your Name.", "choose your gender." -> "Choose Your Gender."
- r37 label: "kana" -> "Kana"

### 8. chunk_04_translated.json -- 2 entries fixed
- r39 stat labels: "up" -> "Up", "pt" -> "Pt"

### 9. chunk_05_translated.json -- 2 entries fixed
- r44 stat labels: "up" -> "Up", "pt" -> "Pt"

### 10. chunk_08_translated.json -- 1 entry fixed
- r49: "trap is set." -> "Trap is set."

## Total: ~1,072 entries fixed

## Casing Rules Applied
| Category | Style | Example |
|----------|-------|---------|
| Item/weapon/armor names | Title Case | "Holy Knight Sword" |
| Monster/NPC names | Title Case | "Bubbly Slime" |
| Menu options/labels | Title Case | "Change Class" |
| Shop/building names | Title Case | "General Store" |
| Trap names | Title Case | "Poison Gas" |
| Stat abbreviations | ALL CAPS | "STR", "MHP", "AGI" |
| Floor labels | ALL CAPS | "B1F", "B10F" |
| UI abbreviations | ALL CAPS | "OK", "ABC", "MP" |
| Dialogue/descriptions | Sentence case | "Welcome to the inn." |
| Battle fragments (follow char name) | lowercase | "has fled!" |

## Not Changed (intentionally lowercase)
- Battle message fragments that follow character names: "was cursed", "has fled!", "inspects the chest"
- These are concatenated after a character name at runtime, so lowercase is correct
