# Translation Mapping: Items & Monsters (Resources 34, 36)

## Summary

Produced **186 translation entries** mapping decoded Japanese game text to English equivalents:
- **29 entries** from Resource 34 (magic stones, talismans, hair ornaments, wristbands, boots)
- **157 entries** from Resource 36 (monster names)

Output written to: `data/translations_items_monsters.json`

## Resource 36 - Monster Names

### Direct Katakana Matches (high confidence)
The vast majority of Resource 36 entries are straightforward katakana transliterations that match 1:1 with glossary monster names. Examples:
- バブリースライム = Bubble Slime
- ゾンビ = Zombie
- ケルベロス = Cerberus
- ヴァンパイア = Vampire
- ファイアドラゴン = Fire Dragon

### Variant Entries
The game has many duplicate/variant monster entries (suffixed with a/b/c or repeated). These appear to be:
- **Palette swaps or difficulty variants** of the same base monster
- **Boss encounter versions** (e.g., multiple アシラ entries for different battle phases)
- **Duplicate thief/ninja progressions** for different dungeon floors

### Uncertain Mappings (flagged with notes)
| Message | Japanese | Mapped English | Issue |
|---------|----------|---------------|-------|
| 26 | オーガロード | Ogre Rogue | JP reads "Ogre Lord" but glossary says "Ogre Rogue" |
| 57 | ブシン | Bushwacker | Abbreviated form, may be different monster |
| 59 | ハイウェイマン | Pied Piper | "Highwayman" mapped to second Pied Piper entry |
| 85 | マイナーダイミョウ | Chicken Ogre | "Minor Daimyo" - contextual match |
| 86 | メジャーダイミョウ | Champion Samurai | "Major Daimyo" - contextual match |
| 94 | ゴースト | Skedim Ghost | Generic "Ghost" entry |
| 95 | ライフスティーラー | Deathbringer | "Life Stealer" - mapped via glossary proximity |
| 128 | ダフネ | Starfish | "Daphne" - needs verification |
| 133 | ストラス | Seraph | "Stolas/Stras" - angel demon, mapped to Seraph |
| 140/157 | 強の壁 | Maelific | "Wall of Strength" - boss label |

### Missing from Decoded Text (in glossary but not found)
- Berseker (level 90, separate from Berserker)
- Some level-specific variants may map differently than assumed

## Resource 34 - Equipment/Accessories

### Categories Found
1. **Magic Stones** (魔石) - messages 1-7: Consumable items with various effects
2. **Talismans** (罰■) - messages 8-15: Matched to glossary talisman list by keyword (飾り=Decorative, 侍=Samurai, 聖王=Holy Knight, etc.)
3. **Hair Ornaments** (■飾り) - messages 16-22: Matched by prefix keywords (ラピス=Lapis, エルフ=Elf, 聖女=Saint, 銀=Silver, 水=Water)
4. **Wristbands** (リスト) - messages 23-28: Direct katakana matches (オーク=Orc, オーガ=Ogre, etc.)
5. **Boots** - message 29: スピードブーツ = Boots of Speed

### Decoding Quality Issues
Resource 34 has several partially-decoded entries (marked with ■):
- The "罰■" suffix on talismans is likely 罰符 or similar
- "■飾り" prefix on hair ornaments is likely 髪飾り (hair ornament)
- Message 14 at only 42% decode rate is the least reliable mapping

## Methodology
- Monster names: Matched katakana transliterations against glossary monster list
- Items: Matched by combining partial kanji readings with glossary item categories
- All entries include `source` field ("glossary" or "guide") indicating match origin
