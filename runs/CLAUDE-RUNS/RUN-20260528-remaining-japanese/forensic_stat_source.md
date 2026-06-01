# Forensic Analysis: Chargen Stat Label Source

## Save State Analyzed
- File: `RAMdumps/27-5.p2s` (7.9MB, created May 31 2026)
- Screen: Character generation stat allocation screen
- EE RAM extracted: 32MB (`eeMemory.bin`)

## Key Finding: R38 IS the Source, and It IS Patched

### R38 Resource Structure (type01)
The original R38 (`extracted/packdata_raw/0038_type01.raw`, 8192 bytes) contains stat labels as FFFF-delimited messages:

| Msg # | Offset | Original (JP)    | Patched (EN) |
|-------|--------|------------------|--------------|
| 0     | 0x0304 | hp               | hp           |
| 1     | 0x030A | hp/mhp           | hp/mhp       |
| 2     | 0x031C | 力 (chikara)     | str          |
| 3     | 0x0322 | 知恵 (chie)      | int          |
| 4     | 0x032A | 信仰心 (shinkou) | fth          |
| 5     | 0x0334 | 生命力 (seimei)  | vit          |
| 6     | 0x033E | 敏捷度 (binshou) | agi          |
| 7     | 0x0348 | 幸運度 (kouun)   | lck          |
| 8     | 0x0352 | 名前             | name         |
| 9     | 0x035A | レベル           | level        |
| 10    | 0x0364 | 種族             | race         |
| 11    | 0x036C | 性別             | gender       |
| 12    | 0x0374 | 属性             | align        |
| 13    | 0x037C | 職業             | class        |
| 25    | 0x03FE | 男               | 男 (kept JP) |
| 26    | 0x0402 | 女               | 女 (kept JP) |

### Patched R38 Location
- File: `build/packdata_resources/0038_type01.raw` (10240 bytes)
- Born: May 23, Modified: June 1
- Format: type01 with FFFF-delimited glyph-ID messages

### R38 in EE RAM
The PATCHED (English) R38 data IS loaded in RAM at **0x00E14300**:

```
0x00E14300: Pointer table (BE uint32 offsets to messages)
0x00E14384: Message data starts
  msg 0: hp
  msg 1: hp/mhp  
  msg 2: str      <-- ENGLISH
  msg 3: int      <-- ENGLISH
  msg 4: fth      <-- ENGLISH
  msg 5: vit      <-- ENGLISH
  msg 6: agi      <-- ENGLISH
  msg 7: lck      <-- ENGLISH
  msg 8: name
  msg 10: race
  msg 11: gender
  msg 12: align
  ...
```

A second copy exists at **0x012B2920** with context:
```
0x012B2880: "change to str" FFFF "change to int" FFFF ...
0x012B2920: mhp | str | int | fth | vit | agi | lck
```

### Japanese Stat Labels: NOT in RAM as MSG Data
- The original Japanese stat label patterns (e.g., `015A FFFE FFFF 0217 02CD FFFE FFFF`) are **NOT found** in RAM
- Only the English equivalents (`0033 0034 0032 FFFF 0029 002E 0034 FFFF`) are present
- The Japanese glyph IDs (力=346, 知恵=535+717, etc.) only appear in flowing dialogue text at 0x00E1xxxx-0x00E2xxxx, not as standalone labels

## EXE Code Analysis

### Text Loading Functions
- `0x00180EF0`: Resource flag check function (checks if resource is loaded)
- `0x00180F20`: Resource flag set function 
- `0x00180FD0`: Full resource loading function (calls 0x00434BE0 and 0x00492D10)

### Chargen Code (0x0019E000 - 0x001A0000)
The chargen screen has three code paths:
1. **0x0019E1C0**: Loads R38 slots 8 (name), 1 (hp), 2 (stat labels) -- "parameter allocation" screen
2. **0x0019E880**: Same R38 calls (second variant)
3. **0x0019EC30**: Loads R63 (!) slots 8, 1, 2 -- third variant (R63 is a class parameter data table, NOT text)

### Slot Index Table in EXE Data
At vaddr **0x004C1F40**:
```
01 02 03 04 05 06 07 08 09 0A 0B 15
```
This is an array of R38 slot indices: 1 (hp/mhp), 2-7 (stat labels), 8 (name), 9 (level), 10 (race), 11 (gender), 21 (?).

### Hardcoded Glyph References in EXE
Some glyph IDs are hardcoded in the EXE (NOT from R38):
- 0x001EBF5C: `addiu $a0, $zero, 0x0217` (glyph 535 = 知)
- 0x0047CA34+: `addiu $reg, $zero, 0x01FF` (glyph 511 = 性) at multiple locations
- These could be used for rendering text outside the R38 message system

## The Paradox: English in RAM, Japanese on Screen

### Timeline
- May 23: R38 patched file created
- May 31: Save state 27-5.p2s captured
- June 1: PACKDATA.DIG last rebuilt, R38 last modified

### Explanation
The save state screenshot shows Japanese stat labels (力, 知恵, etc.) and field headers (性別, 種族, 属性) despite the ENGLISH R38 data being loaded in RAM. This is paradoxical.

Possible explanations:
1. **Rendering Cache**: The game renders stat labels to a GS VRAM texture once when entering the screen. The screenshot captures the GS state (rendered image) which may have been rendered from an older R38 load, while the EE RAM was updated with the new R38 data after rendering.

2. **Multiple Load Points**: The chargen screen may load R38 at screen entry (to render labels) and again during stat allocation. The save state captured after re-loading but before re-rendering.

3. **Different Rendering Source**: Some labels might be rendered by EXE code that uses hardcoded glyph IDs rather than R38 slots. The EXE has hardcoded references to glyph 0x01FF (性) and 0x0217 (知) in the data section.

## Conclusion and Recommendations

**R38 IS the correct resource to patch for stat labels.** The patched R38 at `build/packdata_resources/0038_type01.raw` already contains English translations for all stat labels and field headers (slots 2-17).

### Action Items
1. **Verify the current ISO build** includes the patched R38 -- rebuild PACKDATA.DIG and ISO
2. **Take a NEW save state** with the latest build to confirm stat labels render in English
3. **Check for uppercase glyph support** -- the English labels use uppercase glyph IDs (0x0041-0x005A = A-Z) which must have corresponding glyphs in the font atlas
4. **Investigate EXE hardcoded glyphs** -- addresses 0x001EBF5C, 0x0047C96C, 0x0047CA34 may render Japanese text bypassing R38

### Resources NOT Containing Stat Labels
- R35 (type02): System menu (save/load/options)
- R36-R37 (type01): Other data
- R39 (type15): Item/spell descriptions (mentions stats in sentences but not labels)
- R63 (type01): Class parameter data table (not text)

### Key RAM Addresses
| Address      | Content |
|-------------|---------|
| 0x00E14300  | R38 pointer table |
| 0x00E14384  | R38 message data (ENGLISH) |
| 0x012B2920  | Second R38 copy with "change to X" context |
| 0x00E1xxxx  | Dialogue text containing stat words in sentences |
| 0x004C1F40  | EXE data: R38 slot index array for chargen |
