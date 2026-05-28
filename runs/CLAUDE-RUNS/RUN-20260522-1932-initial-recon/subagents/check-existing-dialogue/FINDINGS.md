# Check: Is Start-Game Dialogue Already in Translated Chunks?

**Date**: 2026-05-22
**Verdict**: NO. The intro/story dialogue is NOT in our translated chunks. It lives in completely different resources (636-927) that have not been decoded or translated.

---

## 1. What Resources Do Our Translated Chunks Cover?

All 10 translated chunk files (chunk_00 through chunk_09) plus the two fix files (chunk_r38_fix.json, chunk_r43_fix.json) cover **resources 34-49 only**, with the exception of a few garbled/binary artifacts:

| Resource | Count | Content |
|----------|-------|---------|
| 34       | 25    | Item names (magic stones, equipment) |
| 35       | 19    | More item names |
| 36       | 156   | Monster/enemy names, NPC class titles |
| 37       | 13    | Character input screen, kana tables |
| 38       | 176   | Character stats, class descriptions, personality traits |
| 39       | 84    | Equipment/stat labels, level-up messages |
| 40       | 55    | Adventurer Guild (registration, party management) |
| 41       | 17    | Salem Church (healing service menu) |
| 42       | 13    | Inn (rest/level-up service menu) |
| 43       | 26    | Bar/Tavern (medal game, quest board, drinks) |
| 44       | 57    | Guild/Automata (synthesis, companion management) |
| 45       | 191   | Shop (Vigger Shop - buying/selling/orders) |
| 46       | 7     | Bulletin Board (community messages) |
| 47       | 29    | Battle/dungeon messages |
| 48       | 107   | Battle system messages (combat, treasure) |
| 49       | 109   | Dungeon exploration text (room descriptions) |
| 1053     | 4     | Garbled binary data (not real text) |
| 1908     | 3     | Garbled binary data |
| 2124     | 4     | Garbled binary data |
| 2654     | 32    | Combo/formation battle descriptions |

**Resources outside 34-49**: Only 1053, 1908, 2124, 2654 -- the first three are junk data ("ブベ", "別ベ", "容ベ"), and 2654 is combo attack descriptions. None are story/intro dialogue.

## 2. Keyword Search Results in Translated Chunks

### Keywords Found (all from service/menu text, NOT intro story):

- **"adventurer"**: R40 "Welcome, adventurer" (guild greeting), R38 personality descriptions, R49 dungeon text -- all service/gameplay text
- **"Duhan"**: R46/M1 only -- bulletin board header mentioning the town
- **"labyrinth"**: R46/M3 only -- bulletin board post about the Self Shop in the labyrinth
- **"quest"/"request"**: R43 -- bartender asking about quests (service menu)
- **"welcome"**: R40 guild greeting, R41 church greeting, R42 inn greeting, R45 shop greeting -- all facility greetings
- **"Salem"**: R41 -- Salem Church service menu
- **"guild"**: R44/M1 -- guild service prompt
- **"knight"**: R38 class descriptions, R34/R00 item names
- **"tavern"/"bar"**: R43 -- bar service menu (medal game, quests)
- **"Luna"**: NOT FOUND anywhere in translated chunks
- **"town"/"city"/"arriving"/"newcomer"/"first time"**: NOT FOUND

### Keywords NOT Found:
- Luna (the bartender NPC name)
- Any arrival/newcomer/first-time dialogue
- Any town introduction narrative
- Any world-building exposition
- Any cutscene or story progression text

## 3. What Do Key Facility Resources (41-46) Actually Contain?

### Resource 41 (Church) - 17 entries
Pure service menu: "This is Salem Church. What business brings you here?" / healing prompts / payment messages / "Begone, heretic!" (insufficient gold) / Yes/No choices. **No intro story.**

### Resource 42 (Inn) - 13 entries
Pure service menu: "Welcome to the Inn" / rest prompts / level-up notifications / payment messages / Yes/No. **No intro story.**

### Resource 43 (Bar) - 26 entries
Service menu: bartender greetings / quest board prompts / medal game dialogue (500g per play, prizes, practice) / Yes/No. **No intro story, no NPC introductions, no Luna.**

### Resource 45 (Shop) - 191 entries
Vigger Shop service menu: buying/selling/ordering. **No intro story.**

### Resource 46 (Bulletin Board) - 7 entries
Community messages: bulletin board intro, Miri's canceled request, Self Shop keys question, Vigger Shop hiring, orc workers discussion, 4th floor exploration story. **Flavor text but NOT intro story.**

## 4. Where IS the Intro/Story Dialogue?

### The untranslated_636_927.txt file reveals the answer:

**Resources 636-927 contain the actual story dialogue.** This is a massive collection:
- **136 resources** in this range
- Categories: "story dialogue", "NPC dialogue", "short dialogue/event"
- **17 resources have FF01 speaker tags** (NPC dialogue with named speakers): R747, R749, R754, R759, R776, R781, R800, R822, R834, R836, R838, R896, R899, R900, R901, R906, R916

### Key story resources:
- **R838**: 1,846 messages with speaker tags -- likely the MAIN NPC dialogue resource
- **R896**: 947 messages with speaker tags -- another massive NPC dialogue resource
- **R899**: 49 messages with speaker tags (944KB file)
- **R900**: 16 messages with speaker tags (705KB file)
- **R901**: 12 messages with speaker tags (378KB file)

These are NOT in full_decoded_text.json and NOT in any translated chunk. They are raw binary with heavy hex encoding -- not yet decoded through the glyph map.

### full_decoded_text.json covers only:
Resources 34-49 plus the junk resources (720, 1053, 1908, 2124, 2654) = **1,168 entries total**. This is purely the menu/UI/gameplay text layer.

## 5. Conclusions

1. **The intro story dialogue is NOT in our translated chunks.** Our chunks cover resources 34-49 exclusively, which are menu/UI/facility/battle text.

2. **The intro story lives in resources 636-927**, which are a completely separate set of binary files that have not been decoded or translated. These contain thousands of messages including NPC dialogue with speaker tags.

3. **No translation was "missed" or "not injected."** The story dialogue simply has never been extracted from the binary resources, decoded through the glyph map, or translated.

4. **The story companion names** (Hina, Ricardo, Greg, Rui, Sara) appear in translations_menus.json but not in any translated chunk -- further confirming the story layer is untouched.

5. **To get intro dialogue translated**, we would need to:
   - Decode resources 636-927 using the glyph map
   - Identify which specific resources contain the intro/arrival-at-Duhan content
   - Translate them
   - Build an injection mechanism for these new resource types (type02-type05 binary formats, not the type01 format our current injector handles)

## 6. Scale of the Missing Story Content

| Category | Resources | Message Count (est.) |
|----------|-----------|---------------------|
| Story dialogue (no speaker) | ~90 resources | ~4,000+ messages |
| NPC dialogue (with speakers) | 17 resources | ~4,000+ messages |
| Short events | ~25 resources | ~50+ messages |
| General text | ~5 resources | ~200+ messages |
| **Total** | **~136 resources** | **~8,000+ messages** |

This dwarfs our current translated content (1,168 entries across 34-49).
