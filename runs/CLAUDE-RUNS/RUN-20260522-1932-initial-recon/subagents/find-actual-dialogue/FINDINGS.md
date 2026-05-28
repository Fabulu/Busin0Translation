# WHERE NPC DIALOGUE TEXT IS STORED

## DEFINITIVE ANSWER

**NPC dialogue (story text, speaker lines, narration) is stored in the SECTION 2 data of TYPE-2 resources within PACKDATA.DIG.**

This was confirmed by searching for the exact byte sequence of the Ingo dialogue (found in RAM at 0x015E5B86 in lotsoftextgnome.p2s) across the entire 839MB PACKDATA.DIG file.

## Key Discovery

The Ingo dialogue glyph sequence `0404 0461 01CB 0198 0088 0293 00AB 0070 009A 0072 0083 003E` (encoding "nankou furaku no shiro..." / "impregnable castle...") was found at:

- **PACKDATA.DIG absolute offset: 0x191F4388** (421,479,304)
- **Resource 1203 (type 2)**, at relative offset 0x20B88
- Specifically in **Section 2** of R1203, at section-relative offset 0xFC18

The same bytes were NOT found in BSN2_0.DSI, SLPM_653.78 (game EXE), or TEMP1.LZH.

## Resource Structure (Type-2 Resources)

Each type-2 resource has a multi-section layout:

```
Offset  Field
------  -----
0x00    zero (always 0)
0x04    payload_size (section 1 size, LE uint32)
0x08    stride (LE uint32)
0x0C    zero
0x10    section_count (LE uint32, always 1 meaning "1 additional section")
0x14    section2_total_size (LE uint32)
0x18    section2_offset (LE uint32, byte offset from resource start)
0x1C    zero
0x20+   Section 1 data (payload, stride-based structured data)
...
sec2_offset+  Section 2 data (dialogue text as BE uint16 glyph stream)
```

### Section 2 Dialogue Format

The dialogue is stored as a stream of **big-endian uint16** glyph indices, with control codes:

| Code   | Meaning           |
|--------|-------------------|
| 0xFFFF | Message delimiter  |
| 0xFFFE | Line break         |
| 0xFFC0-0xFFC6 | Formatting codes (color/emphasis) |
| 0xFFD0-0xFFD9 | Formatting codes  |
| 0xFFE0-0xFFE5 | Formatting codes  |
| 0xFFF0-0xFFF6 | Formatting codes  |
| 0xFFFD | Unknown control    |
| 0xFB00 | Block start marker |
| 0xFB01 | Block marker       |
| 0xFB04 | Choice/branch marker |
| 0xFE00-0xFE06 | Special controls   |

**Important**: FF01 speaker tags are NOT in Section 2. Speaker name assignment is handled by the game engine at runtime, likely driven by Section 1 data or event scripts. On disc, Section 2 is purely dialogue text without speaker attribution.

### Example: R1203 Message 451 (Ingo's line)

```
FFFF                    <- message start
0404 0461 01CB 0198     <- nan kou fu raku (impregnable)
0088 0293 00AB          <- no shiro de
0070 009A 0072 0083     <- a ro u to
003E                    <- punctuation
FFFE                    <- line break
0178 0207 009C 008D     <- teppeki wo hokoru
...
```

## Scale of Dialogue Data

| Metric | Value |
|--------|-------|
| Type-2 resources with dialogue | ~252-510 (depending on how strictly counted) |
| Total Section 2 bytes | ~10 MB (conservative) to ~144 MB (generous) |
| Total messages (FFFF markers) in R1203 alone | 1,633 |
| Resource index range | R35 to R2659 |

The larger count (510/144MB) includes resources where Section 2 also contains non-dialogue structured data like lookup tables (resources with many FFFF markers but few FFFE line breaks).

## Previously Known vs. Newly Found

| Category | Resources | Type | Where text is |
|----------|-----------|------|---------------|
| Menu/system text | R34-R49 | Various (1,3,15,20) | Section 1 payload, stride-based |
| **NPC dialogue** | **R35, R675-R824, R1041-R1203+, etc.** | **Type 2** | **Section 2, BE uint16 stream** |
| Speaker names | R39 (type 15) | Multiple sections | Separate lookup tables |
| Event scripts | R2028, R2068, etc. | Type 3 | "IECS" format, not text |
| Binary/3D/audio | R2087-R2094 | Type 1 | Not text (coincidental FF01 matches) |

## What This Means for Translation

1. **The dialogue text CAN be patched on disc.** It lives in PACKDATA.DIG Section 2 of type-2 resources.

2. **Speaker names** (like "Ingo", "knight commander") are stored separately (likely in R39 and similar resources) and injected at runtime with FF01/FFF0 tags. These need separate patching.

3. **The existing patch pipeline** (which handles R34-R49 menu/system text) needs to be extended to also handle Section 2 dialogue data in type-2 resources.

4. **Section 2 offset** is stored at resource header offset 0x18 and **Section 2 size** at offset 0x14. When patching, both the section data AND these header fields must be updated.

5. **Resources may need to grow** if English translations are longer than Japanese originals, which means sector reallocation in the TOC.

## Files Referenced

- `C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG` - main game data archive (839 MB)
- `C:\Programmieren\wizardrytranslation\data\dialogue_resource_map.json` - full list of dialogue resources (generated)
- `C:\Programmieren\wizardrytranslation\data\xref_ingo2.json` - Ingo dialogue glyph mapping reference
- `C:\Programmieren\wizardrytranslation\tools\extract_packdata.py` - existing extraction tool (TOC parsing)
