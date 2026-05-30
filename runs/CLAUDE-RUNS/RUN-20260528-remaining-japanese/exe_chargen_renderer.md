# Chargen Screen Rendering: Reverse Engineering Results

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6
**EXE**: `extracted/SLPM_653.78`
**Code range**: VA 0x2ED000-0x2F5000 (file offset 0x1ED080-0x1F5080)

---

## Architecture Summary

The chargen screen uses **two completely separate rendering paths**:

| Component | Rendering Path | Data Source | Translatable via |
|-----------|---------------|-------------|-----------------|
| Sidebar labels (性別/種族/属性/職業) | R1272 glyph tiles | R38 MSG glyph stream | chunk_r38_fix.json (already done) |
| Stat labels (力/知恵/etc.) | R1272 glyph tiles | R38 MSG glyph stream | chunk_r38_fix.json (already done) |
| Race/class/alignment values | R1272 glyph tiles | R38 MSG glyph stream | chunk_r38_fix.json (already done) |
| Personality traits | R1272 glyph tiles | R38 MSG glyph stream | chunk_r38_fix.json (already done) |
| Name entry tab labels (カナ/かな/英数/記号) | R1188 bitmap sprites | EXE Table 2E glyph IDs 6400+ | R1188 pixel editing (NOT done) |
| Name entry buttons (決定/男名/女名) | R1188 bitmap sprites | EXE Table 2E glyph IDs 6405+ | R1188 pixel editing (NOT done) |

---

## Rendering Path 1: R38 Labels via R1272 Glyph Tiles

### Call chain (confirmed by disassembly)

```
Chargen main render (VA ~0x2F06B4)
  |
  +-- JAL 0x494350          ; Set up R1188 as background texture
  |
  +-- JAL 0x2F1090          ; chargen_render_A: load glyph-type items
  |     |
  |     +-- JAL 0x301E90    ; Store (slot_type, R38_msg_index) into label array
  |     |                   ; label array at GP-relative offset, max 433 slots
  |     +-- JAL 0x180FD0    ; Check/load resource for bitmap items (icon sprites)
  |
  +-- JAL 0x2F1280          ; chargen_render_B: update dirty labels
  |     |
  |     +-- JAL 0x302020    ; Mark slot as dirty in bitmask at VA 0x565110
  |     +-- JAL 0x302180    ; Mark slot as dirty in bitmask at VA 0x5650D0
  |     ;
  |     ; Iterates linked list: node+0=next, node+4=type(0/1/2),
  |     ; node+6=value(uint16 R38 msg index), node+8=update_flag
  |
  +-- JAL 0x2F13B0          ; chargen_render_C
  |     +-- JAL 0x181070    ; Render helper (calls 0x180F20, 0x180F50 leaf funcs)
  |
  +-- JAL 0x2F1430          ; chargen_render_D
  |     +-- JAL 0x181D20    ; Render helper (calls 0x181CA0 leaf func)
  |
  +-- JAL 0x2F15F0          ; Final rendering pass
  +-- JAL 0x1BF140          ; Text system commit
  +-- JAL 0x2EEFD0          ; Chargen state update
  +-- JAL 0x496510          ; GPU flush/sync
```

### How R38 messages reach the screen

1. The chargen code builds a **linked list of label descriptors** in RAM
2. Each descriptor contains: `{next_ptr, type, R38_msg_index, update_flag}`
3. `chargen_render_A` calls `0x301E90` to store these into a **label slot array** (max 433 entries)
4. `chargen_render_B` calls `0x302020/0x302180` to mark slots dirty in **bitmask arrays** at VA 0x565090/0x5650D0/0x565110 (three layers for types 0/1/2)
5. A separate text system render pass (driven by `0x1BF140` and the 0x18xxxx functions) reads the dirty slots, looks up the corresponding R38 message (BE uint16 glyph ID stream), and renders each glyph from the **R1272 font atlas**

### Key evidence: no direct glyph rendering calls from chargen

The chargen code range (0x2ED000-0x2F5000) contains **zero** JAL calls to the glyph rendering functions at VA 0x303E00-0x306000. This confirms the chargen code only populates a label table -- the actual glyph-to-pixel rendering is handled by the generic text system, which is called indirectly via 0x1BF140.

### R38 message assignments

The R38 MSG resource (7,512 bytes, type-01) contains 260+ messages using BE uint16 glyph IDs from R1272:

| R38 MSG Group | Content | Count | Translation Status |
|--------------|---------|-------|-------------------|
| 0-7 | Stat labels (HP, STR, INT, FTH, VIT, AGI, LCK) | 8 | Done |
| 8-17 | Field headers (name, level, race, gender, etc.) | 10 | Done |
| 18-24 | Spell levels (lv1-lv7) | 7 | Done |
| 25-26 | Gender (male/female) | 2 | MSG 25 BROKEN (has lv7 duplicate) |
| 29-34 | Race names | 6 | Done |
| 37-52 | Class names | 16 | Done |
| 53-86 | Personality traits | 34 | Done |
| 87-144 | Descriptions (personality) | 58 | Done |
| 145-166 | Descriptions (race/alignment) | 22 | Done |
| 148-156 | Alignment labels | 9 | BROKEN (off-by-one shift) |
| 167-218 | Class descriptions | 52 | Done |
| 229-257 | Reputation labels | 29 | Done |

---

## Rendering Path 2: R1188 Bitmap Sprites (Name Entry Tabs/Buttons)

### Call chain

```
Name entry render (VA ~0x2F0780)
  |
  +-- JAL 0x494350          ; render_bitmap_glyph(glyph_id=0)
  |                         ; Sets up R1188 texture as current sprite source
  |
  +-- JAL 0x4964A0          ; Render UI using callback table
       |
       +-- (runtime) reads EXE Table 2E glyph IDs (6400-6412)
       +-- JAL 0x494350     ; For each tab: render_bitmap_glyph(glyph_id)
            |
            +-- group = glyph_id >> 8  (= 0x19 = 25)
            +-- index = glyph_id & 0xFF (= 0..12)
            +-- BSS lookup: 0x4EB100 + group*8 -> texture page info
            +-- BSS lookup: 0x4EB104 + group*8 -> UV rect base
            +-- reads UV at base + index*8: (u, v, flags)
            +-- JAL 0x474D30  ; GS draw textured sprite at UV coords
```

### Tab/button glyph IDs (EXE Table 2E at file 0x3C9DA0)

| Glyph ID | Hex | Japanese | English Needed |
|----------|-----|----------|---------------|
| 6400 | 0x1900 | カナ (Katakana) | Kana |
| 6401 | 0x1901 | かな (Hiragana) | Hira |
| 6402 | 0x1902 | 英数 (Alphanumeric) | ABC |
| 6403 | 0x1903 | 記号 (Symbols) | Sym |
| 6405 | 0x1905 | 決定 (Confirm) | OK |
| 6406 | 0x1906 | 男名 (Male Name) | M.Name |
| 6407 | 0x1907 | 女名 (Female Name) | F.Name |
| 6408 | 0x1908 | 1文字消す (Delete) | Del |
| 6409 | 0x1909 | 全消去 (Clear) | Clear |

### Why these CANNOT use R1272 glyph tiles

The EXE Table 2E stores **one uint32 glyph ID per tab**. The bitmap sprite renderer (`0x494350`) draws exactly ONE pre-rendered sprite per call. There is no loop to compose multi-character strings from individual R1272 glyphs. Replacing a single bitmap glyph ID with ASCII character IDs would require patching the rendering loop -- not feasible without significant code injection.

---

## Answer to Key Questions

### Q1: Do sidebar labels use R1272 glyph IDs or R1188 bitmap glyph IDs?

**R1272 glyph IDs**, via R38 MSG glyph streams. The chargen code stores R38 message indices into a label slot array, and the generic text system renders the corresponding glyph sequences from R1272.

### Q2: Which specific R1272 glyph IDs?

The R38 messages reference R1272 glyph IDs including:
- Sidebar: 513,514 (種族), 511,512 (性別), 515,511 (属性), 504,517 (職業)
- Stats: 346 (力), 535,717 (知恵), 308,354,320 (信仰心), 718,696,346 (生命力), etc.
- These are replaced at build time by the translation pipeline with ASCII glyph IDs (a=33..z=58)

### Q3: Can we just replace R1272 font tiles?

**Already done.** The translation pipeline replaces R38 glyph streams with English ASCII equivalents, and the R1272 font atlas already contains Latin glyphs at IDs 33-58 (a-z). No additional font tile work needed for sidebar/stat labels.

### Q4: What about tab labels?

Tab labels (カナ/かな/英数/記号) use a **completely separate rendering path** via R1188 bitmap sprites. These require either:
- **Option A**: Edit R1188 PSMT4 pixel data at the original Japanese UV positions (need to find exact UV coords)
- **Option D (recommended)**: Edit R1188 pixels at unused rows AND patch R1188's sprite metadata header to redirect UV coordinates

---

## Simplest Fix Path (per component)

| Component | Fix | Effort | Status |
|-----------|-----|--------|--------|
| Sidebar labels | Fix chunk_r38_fix.json entries | Trivial | 95% done, MSG 25 broken |
| Stat labels | Already translated in chunk | None | Done |
| Alignment labels | Fix off-by-one in chunk MSG 149-156 | Trivial | NEEDS FIX |
| Male gender label | Fix chunk MSG 25 (has lv7 duplicate) | Trivial | NEEDS FIX |
| Tab labels (カナ etc.) | Edit R1188 pixels at correct UV positions | Medium | NOT STARTED |
| Buttons (決定 etc.) | Edit R1188 pixels at correct UV positions | Medium | NOT STARTED |
| Name entry kana grid | No translation needed (input keyboard) | None | N/A |

### Immediate actions required:
1. Fix 9 entries in `chunk_r38_fix.json` (MSG 25 and MSG 149-156)
2. Decode R1188 sprite metadata to find UV coordinates for glyph group 0x19
3. Edit R1188 PSMT4 atlas at those UV positions with English labels
4. Re-add R1188 patching step to `build_full_english_v2.py`

---

## Function Reference Table

| VA | File Offset | Purpose |
|----|-------------|---------|
| 0x2ED000 | 0x1ED080 | Chargen initialization |
| 0x2ED2EC | 0x1ED36C | R1188 resource acquisition (lui a0, 0x04A4) |
| 0x2F06B4 | 0x1F0734 | Main render: JAL 0x494350 (bitmap sprite setup) |
| 0x2F1090 | 0x1F1110 | chargen_render_A: populate label slots |
| 0x2F1280 | 0x1F1300 | chargen_render_B: mark dirty labels |
| 0x2F13B0 | 0x1F1430 | chargen_render_C: render pass |
| 0x2F1430 | 0x1F14B0 | chargen_render_D: render pass |
| 0x301E50 | 0x201ED0 | Label array store (slot < 433) |
| 0x301E90 | 0x201F10 | Label array lookup + message resolve |
| 0x302020 | 0x2020A0 | Dirty bitmask setter (3 layers for types 0/1/2) |
| 0x302180 | 0x202200 | Dirty bitmask setter variant |
| 0x180FD0 | 0x081050 | Resource load check (icon sprites) |
| 0x1BF140 | 0x0BF1C0 | Text system commit/flush |
| 0x494350 | 0x3943D0 | Bitmap glyph renderer (R1188 sprites) |
| 0x494050 | 0x3940D0 | Glyph ID resolver (BSS table lookup) |
| 0x4964A0 | 0x396520 | UI callback-driven renderer |
