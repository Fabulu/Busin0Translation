# Resource 46 Inference Findings

## Resource Structure
- **File**: `0046_type03.bin` (18,740 bytes)
- **Format**: type03 with 2 sub-resource headers (16 bytes each) at offset 0x00
- **Message count**: 98 messages (BE uint16 count at 0x20, pointer table at 0x22)
- **Pointer table**: 98 x 4-byte BE uint32 offsets, relative to end of table (0x1AA)
- **Message data**: Big-endian uint16 glyph stream, FFFF delimiters
- **Content**: Tavern Message Board (bulletin board) - community posts by NPCs

## FF01 Speaker Tags
- 83 FF01 tags found across 98 messages
- Format: `FF01 [name_glyphs] FFF0 [dialogue_glyphs]`
- FF01 tags mark highlighted text (speaker names, item names, location names)
- FF03 also appears (MSG 3) as an alternate control code

## Key Findings

### 1. Complete Katakana Table Derived (IDs 193-273)
Verified against 8 anchor points in existing `msg_glyph_map.json`:
- ア=193 through ン=238 (46 basic katakana)
- ガ=239 through ド=253 (15 dakuten)
- バ=254 through ポ=263 (10 handakuten)
- ャ=264 through ヴ=273 (10 small/special)

**53 new katakana mappings** added (those not already in the map).

### 2. Critical Corrections to Existing Map
- **198 = カ (not 鍵)**: The existing map has `"198": "鍵"` but all contextual evidence proves it is カ (katakana). カギ(=key) in MSG 4, ピカピカ in MSG 20, カウンター in MSG 97. Position 193+5 = 198 confirms katakana table placement.
- **369 = 見 (not 明)**: Every usage in r46 reads as 見: 見つかって(found), 見た(saw), 見てきた(have been watching). Never used as 明.

### 3. Digit Table (IDs 16-25)
- 16=0, 17=1, 18=2(existing), 19=3, 20=4, 21=5, 22=6, 23=7, 24=8, 25=9
- Confirmed via dungeon floor numbers (地下N階 = BNF), street address (124-3), currency (10000G), and year references (600年前).

### 4. Font Variant Duplicates
The game font atlas contains duplicate glyphs for the same kanji, likely from multiple font sheets:
- 314/978 = 階 (floor)
- 298/538 = 迷 (labyrinth)  
- 277/573 = 宮 (palace)
- 330/749 = 言 (say)
- 733/396 = 教 (teach)
- 475/296 = 王 (king) - needs verification
- 281/647 = 使 (use) - needs verification

### 5. Decoded Character/Location Names
| Japanese | English | Glyph IDs |
|----------|---------|-----------|
| ドゥーハン | Duhan | 253+269+93+218+238 |
| オリアーナ | Oriana (princess) | 197+232+193+93+213 |
| テュルゴー | Turgot (ninja) | 211+265+233+243+93 |
| ウェブスター | Webster (villain) | 195+270+256+205+208+93 |
| ジャンケンマン | Jankenman (NPC) | 245+264+238+201+238+223+238 |
| セルフショップ | Self-Shop (dungeon shop) | 206+233+220+204+266+272+261 |
| カルマン | Karman (labyrinth name) | 198+233+223+238 |
| ホビット | Hobbit (monster) | 222+255+272+212 |
| インプ | Imp (monster) | 194+238+261 |
| ボギーキャット | Bogie Cat (monster) | 258+240+94+199+264+272+212 |
| パメラ | Pamela (NPC) | 259+226+231 |
| ミリ | Miri (NPC) | 224+232 |
| サンゴート | San-Goth (country) | 203+238+243+93+212 |
| オートマタ | Automata (enemy type) | 197+93+212+223+208+93 |
| ベノアン書店 | Venoan Bookstore | 257+217+193+238+1014+956 |
| ヴィガー商店 | Vigger Shop | katakana+904+956 |

### 6. Decoded Speaker Tags
- 騎士団 (Knight Order): 280+326+310
- 騎士団長 (Knight Commander): 280+326+310+660
- 冒険者ギルド (Adventurer Guild): 730+419+342+240+233+253

### 7. High-Confidence Kanji (68 total kanji inferred)
Key vocabulary mapped with HIGH confidence:
- 迷宮(538+573)=labyrinth, 冒険(730+419/486+487)=adventure, 依頼(999+892)=request
- 回復(415+413)=recovery, 全滅(653+377)=annihilation, 死神(313+300)=Grim Reaper
- 性格(511+516)=personality, 信頼(308+892)=trust, 探索(574+575)=exploration
- 掲示板(899+376+900)=bulletin board, 商店(904+956)=shop
- 情報(946+965)=information, 期限(935+548)=deadline
- Common: 人(319), 女(349), 子(414), 気(339), 出(497), 行(367), etc.

### 8. Message Board Structure
Messages correspond to numbered bulletin board posts (guide messages #1-#32):
- MSG 0-1: Empty/separator
- MSG 2: Post #1 (setting up bulletin board, by Gin)
- MSG 3-4: Post #4 and follow-ups (Miri asking about magic)
- MSG 5-7: Post #25 (Vigger Shop part-time workers)
- MSG 8: Adventurer anecdote (Hobbit + Imp story)
- MSG 9: Post #21 (Karman Labyrinth tour contest)
- MSG 10: Post #9 (Bogie Cats are cute)
- MSG 11: Post #2 (Venoan Bookstore address change)
- MSG 12-13: Post #4 follow-up (how to learn magic)
- MSG 14: Post #8 (Vigger Shop interview results)
- MSG 15-16: Post #10 (Jankenman rock-paper-scissors)
- MSG 17-18: Post #5 (labyrinth exploration tips)
- MSG 19: Post #15 (personality compatibility - Samurai)
- MSG 20: Post #5-2 (leveling up signs)
- MSG 21-23: Post #3 (Princess Oriana nostalgia)
- MSG 24-28: Post #6 (Witch Aurora discussion)
- MSG 29: Post #6-3 (Simson diary)
- MSG 30: Post #12 (Vigger Shop orders announcement)
- MSG 31: Post #7 (recovery fountain)
- MSG 32: Post #11 (Order killed again)
- MSG 33-34: Post #11-1 (witch torture)
- MSG 35-37: Post #15 (personality - Samurai follow-up)
- MSG 41-47: Post #22 (Vigger Shop reviews - Pamela)
- MSG 48-50: Post #6-3-2 (Simson, witch eating monsters)
- MSG 51-57: Post #17 (Turgot survived the witch)
- MSG 58-59: Post #20 (deleted message)
- MSG 60-62: Post #23 (personality 2 - lonely companion)
- MSG 66: Post #5-3 (use the map)
- MSG 67-68: Post #27 (steel dolls / Automata)
- MSG 69-70: Post #28 (Princess returned)
- MSG 71-74: Post #29-32 (Webster, Writhing Demons, Yusu reports)
- MSG 79-80: Post #7 conflict (poison fountain)
- MSG 81: Post #24 (information shop)
- MSG 83-85: Post #13 (diabolical party - Mac Bain)
- MSG 86: Post #24-1 (information shop closing)
- MSG 87-90: Post #14 (stolen requests - Toranmer)
- MSG 91-93: Post #16 (exploration tips - Through magic)
- MSG 94-96: Post #18 (Jankenman bracelet - Virgo)
- MSG 97-98: Post #18-1 (rules violation debate)

## Output
- `data/inferred_r46.json`: 148 new glyph mappings + 2 corrections
  - 53 katakana, 16 digits/special, 79 kanji
  - HIGH confidence: ~95, MEDIUM: ~45, LOW: ~8
