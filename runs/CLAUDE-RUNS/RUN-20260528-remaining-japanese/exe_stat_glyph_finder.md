# EXE Stat Glyph Finder - Results

## Key Finding: Stat Label Glyphs Are NOT in the EXE

The stat label kanji glyph IDs (力=346, 知恵=535+717, etc.) are stored exclusively
in **R38 message data**, not in the EXE. The EXE only stores message *indices* (2-7)
which reference the R38 glyph streams at runtime.

## How the Chargen Stat Label Rendering Works

### Data Flow
```
R38 resource (PACKDATA.DIG res 0038)
  -> loaded into memory at runtime
  -> pointer tables built at VA 0x5650F0 (type0), 0x5650B0 (type1), 0x565090 (type2)
  -> chargen code reads linked list nodes containing (type, msg_index) pairs
  -> R38 renderer fetches glyph stream from pointer table[msg_index]
  -> glyphs rendered from font pages
```

### R38 Message Index -> Stat Label Mapping
```
R38 msg[2]  = 力       (STR)  -> glyphs [346, FFFE]
R38 msg[3]  = 知恵     (INT)  -> glyphs [535, 717, FFFE]
R38 msg[4]  = 信仰心   (PIE)  -> glyphs [308, 354, 320, FFFE]
R38 msg[5]  = 生命力   (VIT)  -> glyphs [718, 696, 346, FFFE]
R38 msg[6]  = 敏捷度   (AGI)  -> glyphs [582, 719, 590, FFFE]
R38 msg[7]  = 幸運度   (LUC)  -> glyphs [720, 721, 590, FFFE]
R38 msg[8]  = 防具     (AC?)  -> glyphs [314, 510, FFFE]
R38 msg[9]  = 経験値   (EXP)  -> glyphs [234, 257, 233, FFFE]
R38 msg[10] = 年齢     (AGE)  -> glyphs [513, 514, FFFE]
R38 msg[11] = 性別     (SEX?) -> glyphs [511, 512, FFFE]
```
(FFFE = line break, FFFF = message terminator)

### EXE Code Locations (for reference)

| Function | VA | File Offset | Purpose |
|----------|-------|-------------|---------|
| Chargen renderer | 0x2F1090 | 0x1F1110 | Iterates linked list, dispatches to R38 renderer |
| Caller 1 | 0x2F0300 | 0x1F0380 | Iterates 40-byte descriptor array, calls chargen renderer |
| Caller 2 | 0x2F06D0 | 0x1F0750 | (another call site) |
| Caller 3 | 0x2F0810 | 0x1F0890 | (another call site) |
| R38 renderer | 0x301E90 | 0x201F10 | Takes (type, index), looks up glyph stream, renders |
| Descriptor builder | 0x2EF6C0 | 0x1EF740 | Parses bytecode script, builds descriptor linked lists |

### Chargen Renderer (VA 0x2F1090) Key Instructions
```
lw   s1, 4(s2)      ; load linked list head (labels)
lh   v0, 4(s1)      ; node type (0=label, 1=?, 2=?)
lhu  a1, 6(s1)      ; R38 message index
jal  0x301E90        ; call R38 renderer
; ... iterates via lw s1, 0(s1) (next pointer at node+0)
```

### R38 Renderer (VA 0x301E90) Table Selection
```
Type 0 -> pointer table at VA 0x5650F0  (runtime, 512 entries max)
Type 1 -> pointer table at VA 0x5650B0
Type 2 -> pointer table at VA 0x565090
```

### ELF Mapping
```
ELF load: file offset 0x80 -> VA 0x100000, size 0x3FDC80
VA = file_offset + 0x0FFF80
file_offset = VA - 0x0FFF80
GP = 0x504FF0
```

## Fix Strategy

### CORRECT Approach: Patch R38 Messages 2-7 (and 8-11)
The stat labels render from R38 glyph streams. To show English labels:

1. Replace R38 msg[2] glyphs with ASCII glyph IDs for "STR"
2. Replace R38 msg[3] glyphs with ASCII glyph IDs for "INT"  
3. Replace R38 msg[4] glyphs with ASCII glyph IDs for "PIE"
4. Replace R38 msg[5] glyphs with ASCII glyph IDs for "VIT"
5. Replace R38 msg[6] glyphs with ASCII glyph IDs for "AGI"
6. Replace R38 msg[7] glyphs with ASCII glyph IDs for "LUC"
7. Replace R38 msg[8] glyphs with ASCII glyph IDs for "AC"
8. Replace R38 msg[9] glyphs with ASCII glyph IDs for "EXP"
9. Replace R38 msg[10] glyphs with ASCII glyph IDs for "AGE"
10. Replace R38 msg[11] glyphs with ASCII glyph IDs for "SEX"

### WHY No EXE Patch is Needed
- The EXE does NOT store glyph IDs 346, 535, 717, etc. for stat labels
- The EXE only stores R38 message indices (small numbers 2-7)
- These indices reference R38's glyph stream data
- The linked list nodes are built dynamically from a bytecode script in resource data
- Patching R38 is sufficient; no EXE binary patch required

### Current Build Status
- R38 resource 0038 has **zero** translations in `encoded_translations.json`
- Messages 2-7 (stat labels) are NOT yet translated
- This is why chargen stat labels still show kanji

### How to Add R38 Translations
Add entries to `data/encoded_translations.json`:
```json
{"resource": 38, "message": 2, "glyphs": [<S>, <T>, <R>]},
{"resource": 38, "message": 3, "glyphs": [<I>, <N>, <T>]},
{"resource": 38, "message": 4, "glyphs": [<P>, <I>, <E>]},
{"resource": 38, "message": 5, "glyphs": [<V>, <I>, <T>]},
{"resource": 38, "message": 6, "glyphs": [<A>, <G>, <I>]},
{"resource": 38, "message": 7, "glyphs": [<L>, <U>, <C>]},
```
Where `<S>`, `<T>`, `<R>` etc. are the halfwidth ASCII glyph IDs from the font atlas.
