# Narration Resource Analysis: R1192, R1193, R1194, R2361
Date: 2026-05-28 (UPDATED - corrects previous analysis)

## Critical Correction

**Previous analysis was PARTIALLY WRONG.** The intro narration text is NOT purely pre-rendered into texture images. R1193 and R1194 contain standard glyph-indexed text (type-2 MSG format with Section 2 glyph data), exactly like all other dialogue in the game. The narration text IS patchable via the existing glyph replacement pipeline.

The previous conclusion was based on:
- Failing to find the text via SJIS string search in the ISO (because it's stored as glyph indices, not encoded text)
- Misidentifying R1192 as containing "TextEventImage texture with baked text" (it contains background artwork, not text)
- EXE strings like `TextEventImageDrawRequest` referring to the background artwork system, not the text overlay

## Resource Format Summary

| Resource | Size | Type | Format | Contains |
|----------|------|------|--------|----------|
| R1192 | 157,696 | 2 | Scene container (GS packets) | Intro background images (map, battles, etc.) |
| R1193 | 6,144 | 2 | MSG (opcodes + glyphs) | Intro narration TEXT part 1 (351 glyphs) |
| R1194 | 8,192 | 2 | MSG (opcodes + glyphs) | Intro narration TEXT part 2 (482 glyphs) |
| R1195 | 2,048 | 2 | MSG (opcodes + 2 glyphs) | Transition/wait control script |
| R2361 | 43,008 | 2 | Scene container (GS packets) | Ending scene backgrounds |

## R1192: Intro Scene Container (NOT text)

**Structure:**
```
Outer header:     0x00-0x1F  (32 bytes)
Section 1:        0x20-0xA8CF  (43,184 bytes)
  Sub-header:     data_size=13152, count=199
  Identity matrix (4x4 float) at 0x2C
  Vertex/geometry data (13,152 bytes)
  Offset table at 0x3380: [0x3380, 0x3550, 0xA4A0, 0xA7E0]
  Scene script commands (0x3550-0xA4A0, ~28KB)
  Glyph lookup palette + animation data (0xA4A0-0xA8D0)
Section 2:        0xA8D0+  (113,032 bytes)
  Magic: 0x13131313
  Count: 199 entries
  PS2 GS transfer packets (background texture data)
```

**Purpose:** Contains the painted background artwork for the intro slideshow (map of Duhan, battle scenes, warrior portrait, city view, devastated landscape, Atlus logo). These 512x512 images were confirmed via PCSX2 texture dumps. The text is NOT in this resource.

127 type-2 resources across the game share the 0x13131313 section 2 format. These are all scene/model containers, not text resources.

## R1193: Intro Narration Text Part 1 (GLYPH-BASED)

**Structure:** Standard type-2 MSG format
- Section 1 (4,800 bytes): TextEvent script opcodes (display timing, positioning, effects)
- Section 2 (702 bytes): 351 glyph indices (uint16 big-endian)

**Decoded text (approximate -- 21 glyphs unmapped):**
```
かつて中[世]紀もの[長]きにわたってベノアの[国]を[恐]と[混]乱に[陥]れた[戦][争]があった。
[実]にバンクォーの[戦][役]と[呼]ばれるものである。
サンゴートの王がドゥーハン[王]国のをかかげ攻め入ってきたのが、
そもそもの[発]端であったが！

[key wait]

かつて中[世]紀もの[長]きにわたってドゥーハン王国を[恐]と[混]乱に[陥]れた[戦][争]があった。
王国の[兵][力]を２／３までに[減][少]させたその[壮][絶]な[戦][況]はバンクォーの[戦][役]と
[人][々]に[記][憶]される。[魔]棒に[取]り[憑]かれたサンゴート王が[死]者を報い、
攻め入ってきたのが、そもそもの[発]端であったが
[戦][禍]はベノア[全][土]に[広]がった。[一]者の[活][躍]が抜れなければ、
ドゥーハン王国は、[国][際]から消えていたであろう。
[実]に[聖]王と[呼]ばれるオルトルードである。
[彼]はサンゴートを[打]ち安り、ドゥーハン王国に[平][和]と[希]強を[取]り戻した。
それから[25][年]...
```

Corresponds to English guide translation: "For thirty years the kingdom of Duhan was plunged into blood and terror..."

**Unmapped glyph indices:** 384, 447, 448, 488, 654, 813, 907, 1027, 1034, 1060, 1089, 1178, 1186, 1187, 1200, 1320, 1342, 1398, 1409, 1483, 65505

## R1194: Intro Narration Text Part 2 (GLYPH-BASED)

**Structure:** Standard type-2 MSG format
- Section 1 (6,274 bytes): TextEvent script opcodes
- Section 2 (964 bytes): 482 glyph indices (uint16 big-endian)

**Content:** Queen Oriana's coronation speech and the aftermath of the Battle of Banquo. Contains the transition from backstory to the game's present day.

**Unmapped glyph indices (40):** 323, 357, 424, 437, 447, 448, 474, 485, 631, 654, 907, 1021, 1022, 1034, 1035, 1051, 1072, 1083, 1106, 1116, 1149, 1152, 1198, 1200, 1277, 1370, 1385, 1419, 1463, 1497, 1525, 1577, 1580, 1684, 1697, 1710, 1720, 1721, 1722, 1723

## R2361: Ending Scene Container

**Structure:** Same format as R1192
- Section 1 (18,308 bytes): sub-data 5032 bytes, count=76, identity matrix, scene commands
- Section 2 (23,480 bytes): 0x13131313 magic, 76 GS packet entries

**Companion resources (from EXE table at 0x3E8F70):**
- R2341: Data resource (paired with R2361)
- R2360 (type 14): Additional scene data
- R2223/R2224 (type 3): Animation/model data

R2361 does NOT contain narration text. No companion type-2 MSG text resource was found nearby. The ending narration text location remains unidentified and needs further investigation (may require PCSX2 gameplay to determine which resources are loaded during ending).

## PCSX2 Texture Dumps

411 textures in `build/pcsx2_dumps/`. The large 512x512 textures (GS page 0x2653) are confirmed intro backgrounds:

| File | Content |
|------|---------|
| `29703fce...-00002653.png` | Map of Duhan/Benoa region |
| `1ab2e82f...-00002653.png` | Atlus logo |
| `e241afe5...-00002653.png` | Battle scene (soldiers) |
| `86b6b455...-00002653.png` | Knights on horseback |
| `4ab4545d...-00002653.png` | Devastated landscape |
| `28c51e47...-00002653.png` | Warrior/king portrait |
| `98131903...-00002653.png` | City view |
| `135fe261...-00002654.png` | Ornate text frame border |

No dumps of narration text exist because text is rendered dynamically via the glyph system.

## EXE Scene Table References

Intro scene table at ELF+0x3C96F0:
- R1193 (text), R1194 (text), R1195 (control), R1196+ (game scenes)

R1192 referenced at ELF+0x3C9A20 as scene container with glyph lookup palette.

R2361 referenced at ELF+0x3E8F70 in ending scene entries.

## Difficulty Assessment

### R1193/R1194 (Intro Narration): MEDIUM
- **Format:** Standard type-2 MSG with glyph indices -- same injection pipeline as all other translated text
- **Blocker:** ~50 unique unmapped glyph indices need identification (kanji used primarily in narration)
- **Approach:** Map missing glyphs via font bitmap analysis, translate text, inject via existing build pipeline
- **No texture editing needed.** No image replacement needed. Standard text translation workflow.

### R2361 (Ending Scene): NEEDS INVESTIGATION
- Scene container only; no text found in R2361 or companion resources
- May require PCSX2 gameplay capture during ending to identify text resources
- Lower priority (endgame content)

## Recommended Approach

1. **Map the ~50 unmapped glyph indices** in R1193/R1194 using font bitmap analysis at specific glyph positions
2. **Translate the narration text** using the English Wizardry guide (data/guide_full_text.txt lines 164-178) as reference
3. **Add R1193/R1194 to the translation injection pipeline** (currently only R1196-R1213 are targeted)
4. **Inject via existing build system** -- these are standard type-2 MSG resources, no special handling needed
5. For R2361 ending: defer until endgame testing reveals which resources contain the ending text

## Key Takeaway

The intro narration text is **glyph-based, not texture-based**. It uses the same rendering system as all other in-game text. The categorization in REMAINING_JAPANESE.md as "pre-rendered TextEventImage textures requiring image editing" was incorrect for the TEXT portion. R1192 contains only the background artwork. R1193/R1194 contain the actual narration text as patchable glyph indices.

The existing `dumps/textevent/` decode attempts and `build/textures_to_edit/R1192_intro_narration.raw` were trying to find text in the WRONG resource (R1192 backgrounds instead of R1193/R1194 glyph data).
