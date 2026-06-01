# Chargen Stat Label Disassembly: ROOT CAUSE FOUND

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6 (1M context)
**Method**: MIPS64 disassembly via capstone + binary data analysis

---

## EXECUTIVE SUMMARY

**The stat labels (STR/INT/FTH/VIT/AGI/LCK) and sidebar labels (alignment, etc.) are rendered from glyph IDs embedded DIRECTLY IN R39 (resource 0039, type-15 script), NOT from R38.**

Previous analyses were WRONG in claiming these labels come from R38. R38 contains the stat labels too, but the chargen screen reads them from R39's inline glyph streams, which contain the Japanese kanji glyph IDs and were never translated.

---

## EVIDENCE

### 1. R39 Contains Japanese Stat Label Glyph IDs

File: `extracted/packdata_resources/0039_type15.bin` (2,462 bytes original)
Build: `build/packdata_resources/0039_type15.raw` (26,624 bytes expanded)

#### Original R39 -- stat labels at offsets 0x06CE-0x0782:

| Offset | Glyph IDs (BE uint16) | Japanese | English |
|--------|----------------------|----------|---------|
| 0x06D0 | 45, 40, 48 | hp (ASCII) | hp |
| 0x06DC | 346 | 力 | STR |
| 0x06EC | 535, 717 | 知恵 | INT |
| 0x06FE | 308, 354, 320 | 信仰心 | FTH |
| 0x0710 | 718, 696, 346 | 生命力 | VIT |
| 0x0722 | 582, 719, 590 | 敏捷度 | AGI |
| 0x0734 | 720, 721, 590 | 幸運度 | LCK |

Second copy at 0x0748-0x0782 (same glyph IDs, different context suffix).

#### Build R39 -- same labels at offsets 0x56D6-0x57BA:

| Offset | Glyph IDs | Label |
|--------|-----------|-------|
| 0x56D6 | 346 | STR (still Japanese) |
| 0x5700 | 535, 717 | INT (still Japanese) |
| 0x572C | 308, 354, 320 | FTH (still Japanese) |
| 0x575A | 718, 696, 346 | VIT (still Japanese) |
| 0x5788 | 582, 719, 590 | AGI (still Japanese) |
| 0x57B6 | 720, 721, 590 | LCK (still Japanese) |

Note: "exp" at 0x58D6 (glyphs 37, 56, 48 = "exp") IS already English.

#### Build R39 -- alignment/sidebar labels also still Japanese:

| Offset | Glyph IDs | Label |
|--------|-----------|-------|
| 0x5816 | 515, 511 | 属性 (alignment) |
| 0x5846 | 515, 511 | 属性 (alignment) |
| 0x5878 | 515, 511 | 属性 (alignment) |

### 2. R39 Has MANY More Japanese Glyphs Throughout

The R39 script contains inline text scattered throughout its 26K data. A scan found:
- **42+** occurrences of glyph 346 (力/STR) across the file
- **16+** occurrences of 属性 (alignment) pairs (515, 511)
- **6+** occurrences of 族 (514, part of race)
- **12+** occurrences of 前 (510, part of "name")
- **6+** occurrences of 能/命 (part of stat descriptions)

These are embedded in descriptive text, tooltip strings, and UI layout scripts -- not just in the stat label display area.

### 3. Disassembly Confirms R39 Is Used by Chargen

#### EXE Code Path (confirmed by disassembly):

```
Chargen main render (VA ~0x2F06B4)
  |
  +-- JAL 0x2F1090  (chargen_render_A)
  |     |
  |     +-- Iterates linked list from descriptor at $s2
  |     +-- lh $v0, 4($s1)   -- type from node+4
  |     +-- lhu $a1, 6($s1)  -- msg_index from node+6
  |     +-- Type 0: JAL 0x301E90 with $a0=0, $a1=msg_index
  |     +-- Type 1: JAL 0x301E90 with $a0=1, $a1=msg_index
  |     +-- Type 2: JAL 0x301E90 with $a0=2, $a1=msg_index
  |
  +-- JAL 0x2F1280  (chargen_render_B)
  |     +-- Iterates linked list from descriptor at $s2+0xC
  |     +-- Marks dirty in bitmask (JAL 0x302020 / 0x302180)
  |
  +-- JAL 0x2F13B0 / 0x2F1430  (render C/D)
  +-- JAL 0x2F15F0  (final render)
  +-- JAL 0x1BF140  (text system commit)
```

#### Key Function 0x301E90 (bitmask check):

```
0x301E90: sign-extend $a0 (type)
          if type < 0 or type >= 13: return 0
          if type == 0: check $a1 < 0x200, then check bitmask at VA 0x565110
          if type == 1: check bitmask at VA 0x5650D0
          if type == 2: check bitmask at VA 0x565090
          Returns 1 if bit is SET, 0 otherwise
```

This function does NOT render -- it checks if a slot is marked dirty. The actual text rendering happens through the generic text system that reads glyph streams from the data pointers stored in the **slot table** at `GP-0x68F4 = VA 0x4FE6FC`.

#### Slot Table Setup:

The chargen init code at 0x2F2400 calls `JAL 0x301E50` (write_slot) with slot indices 0x1AC-0x1B0, storing resource data pointers. These pointers reference the loaded R39 data in RAM.

The generic text system then reads BE uint16 glyph IDs from these data pointers and renders them using the R1272 font atlas.

### 4. Why R38 Translations Don't Fix These Labels

R38 IS translated and IS loaded into RAM (confirmed by save state analysis). However:

- **R38 messages 2-7** contain English stat label glyph IDs (e.g., msg 2 = "str")
- **R39 script data** contains its OWN COPY of the stat label glyph IDs (Japanese kanji)
- The chargen screen renders labels from **R39's inline glyph streams**, not from R38

R38 messages are used by OTHER screens (status screen, equipment screen) for the same stat labels. The chargen screen has its own independent rendering path through R39.

---

## FIX STRATEGY

### Approach: Patch R39 Inline Glyph IDs

The R39 build file (`build/packdata_resources/0039_type15.raw`) must have its inline Japanese glyph IDs replaced with English ASCII glyph IDs.

#### Stat Label Replacements (primary block at 0x56D6-0x57BA):

| Offset | Current (JP) | Replace with (EN) | Notes |
|--------|-------------|-------------------|-------|
| 0x56D6 | 0x015A (346) | 0x0053 (83='s'), 0x0054 (84='t'), 0x0052 (82='r') | Need to INSERT 2 extra uint16s |
| 0x5700-02 | 0x0217,0x02CD | 0x0049 (73='i'), 0x004E (78='n'), 0x0054 (84='t') | Need to INSERT 1 extra uint16 |
| 0x572C-30 | 0x0134,0x0162,0x0140 | 0x0046 (70='f'), 0x0054 (84='t'), 0x0048 (72='h') | Same size, direct replace |
| 0x575A-5E | 0x02CE,0x02B8,0x015A | 0x0056 (86='v'), 0x0049 (73='i'), 0x0054 (84='t') | Same size, direct replace |
| 0x5788-8C | 0x0246,0x02CF,0x024E | 0x0041 (65='a'), 0x0047 (71='g'), 0x0049 (73='i') | Same size, direct replace |
| 0x57B6-BA | 0x02D0,0x02D1,0x024E | 0x004C (76='l'), 0x0043 (67='c'), 0x004B (75='k') | Same size, direct replace |

**WARNING**: STR and INT have different glyph counts than their Japanese equivalents (STR = 3 glyphs vs 力 = 1 glyph; INT = 3 vs 知恵 = 2). Direct byte patching will corrupt the data structure unless the R39 format supports variable-length records or padding.

#### Alignment Label Replacements (0x5816+):

Multiple occurrences of 515, 511 (属性) need replacement with "align" or similar.

#### IMPORTANT: R39 contains ~100+ additional Japanese glyph occurrences throughout its descriptive text. A full translation pass on R39 is needed, not just the stat labels.

---

## KEY ADDRESSES REFERENCE

| Item | Virtual Address | File Offset | Notes |
|------|----------------|-------------|-------|
| Chargen render A | 0x2F1090 | 0x1F1110 | Iterates linked list, checks dirty bitmask |
| Chargen render B | 0x2F1280 | 0x1F1300 | Marks slots dirty/clean |
| Bitmask check | 0x301E90 | 0x201F10 | Tests if slot bit is set |
| Bitmask set | 0x302020 | 0x2020A0 | Sets slot bit |
| Bitmask clear | 0x302180 | 0x202200 | Clears slot bit |
| Slot table write | 0x301E50 | 0x201ED0 | Stores ptr at slot_table[index] |
| Slot table read | 0x301E10 | 0x201E90 | Reads ptr from slot_table[index] |
| Slot table pointer | GP-0x68F4=0x4FE6FC | 0x3FE77C | Points to 433-entry table |
| Dirty bitmask type 0 | 0x565110 | (runtime BSS) | 512 bits for type-0 slots |
| Dirty bitmask type 1 | 0x5650D0 | (runtime BSS) | 512 bits for type-1 slots |
| Dirty bitmask type 2 | 0x565090 | (runtime BSS) | 512 bits for type-2 slots |
| GP register | 0x504FF0 | - | Global pointer base |
| ELF VA base | 0x100000 | file 0x80 | VA = file_offset + 0x0FFF80 |

---

## FILES

- **Original R39**: `extracted/packdata_resources/0039_type15.bin` (2,462 bytes)
- **Build R39**: `build/packdata_resources/0039_type15.raw` (26,624 bytes)
- **EXE**: `extracted/SLPM_653.78` (4,185,776 bytes)
