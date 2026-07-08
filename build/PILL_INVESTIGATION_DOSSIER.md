# Item-name pill widening — investigation dossier (2026-07-08)

## v180 UPDATE (2026-07-08 evening) — fix BUILT, two findings below FALSIFIED
**Read this section first; the sections below are kept for history but two of
their claims are wrong.**

FALSIFIED:
1. *"Seven 188x24 pill records at 0xdca192"* — a MISALIGNED parse. The packed
   10-byte records' byte +9 is unwritten malloc garbage (parser 0x490D20 writes
   only 9 bytes: sh@0/2/4/6 + sb@8), and the walk-back anchored 2 bytes into the
   stream ("u=1801" = the previous record's page byte 0x09 + garbage 0x07 read
   LE). True array base = 0xdc9f00 (static ptr @0x5652B4 points at it); the
   correctly-aligned records there are seven 24x12 tiles at v=188 — unrelated.
   Beware: 20-byte-stride BE tables also alias at 4-byte offsets — only trust
   records at table-parsed boundaries.
2. *Candidate site 0x170E98 (tiles 185/186 vs 187/188)* — that module
   (0x170xxx–0x172xxx) is the SHOP module; tiles 184-186 (group 1/2) are the
   big torn-parchment dialog box (R2139 sub10: 256x256 sheet, 40px cap strips),
   drawn by the 3-part widget 0x13F590 whose only two callers (0x1414F4 banner,
   0x144A54) both pass fixed t1=0x1D0(464). Neither is the pill. The
   0x172230/0x172384 "element 189" draw needs ui-slot-8 (@0x566C90+0x40) which
   is NULL in both evidence saves — also not the pill.

PROVEN (pill architecture):
* Pill ART = R2138 **sub27** (256x256 PSMT4 atlas @0x16D4F0, pixels @+0x740),
  box band (0,136)-(192,200): double-line left cap x0..6, rails, right border
  x184..186 + bracket serifs to x189; band columns 190..255 are 100% index 0.
* Pill GEOMETRY = R2139 (2139_type15.raw, 6144B, {id,size,off} sub directory)
  **sub13 rec2** = BE u32 {u=0, v=136, w=192, h=64, page=3} at file 0x1220.
  Same art in the treasure scene comes from a **different resource** (R1364-
  family; R2139 is NOT loaded there) — treasure-side geometry still unlocated.
* Handle chain: group1/2 handle table @0x4B61F0 (12B entries: w0=R2138-sub id,
  +4=handle→R2139 sub, resolved 0x492A70/0x492700), tile-entry table @0x4B6340.
  Tiles 187..191 = R2139 sub13 recs 0..4; the box record = tile 189.
  Group0→R2147/R2148 (tavern), g3→R2141/R2142, g4→R2144/R2145, g5/11→R2150/53.
* On-screen: shop pill ≈192-198px wide (≈ natural 192), treasure ≈196x25,
  shop ≈x24..222 h≈33 — same art, different vertical scale.

FIX SHIPPED (v180, option 1 resource-side, tools/patch_pill_widen.py, in
build_v9 Step 6.5 after patch_r2138; gates tests/test_pill_widen.py):
R2139 sub13 rec2 w 192→256 (2 bytes @0x122A) + sub27 band re-ink
(rows 136..199: new[176..256)=old[112..192) — border now x248..250).
Data-only; EXE untouched; battle arena untouched.

ONE BOOT MUST ANSWER (build/BUSIN0_EN_v180_pill.iso, md5 78f6d8a3ad44ff9de7…):
buy/inspect at the pill/alchemy shop (Magic Stones synthesis list) —
(a) capsule wider (~256px) → natural-width draw PROVEN, shop pill improved;
(b) capsule unchanged with art compressed ~1.33x → explicit-width draw → next
step is the caller's width computation via live debugger.
Note: even at 256px, 17+-char names at the current JP-width text pitch/anchor
still overflow somewhat — the complete cure also needs the text anchor fix
(same live-debug session as the name/quantity overlap,
build/ALCHEMY_SHOP_OVERLAP_SPEC.md). The treasure-scene pill is a separate
draw (R1364-family) and is expected UNCHANGED in v180; pinning it wants a GS
draw-dump at a treasure chest.
Fallback if widening misbehaves: blank the sub27 band pixels (suppress the
capsule art, resource-side; no call site needed) — and the treasure twin can
be suppressed the same way once its atlas offset is known.

## Goal
Widen (or otherwise fix) the treasure/alchemy item-name capsule ("pill") so long English
item names ("Town Return Potion", "Zateal Spell Book") don't spill past its rounded caps.
The old attempt (EXE imm @0x13F688 185→440) is WITHDRAWN — that immediate is the chargen
banner middle TILE ID, and patching it caused the v175–v178 white-banner regression
(see build/BANNER_PROBLEM_HANDOFF.md "SOLVED" section).

## Visual ground truth
`ramdumps/_townreturnpotion_shot.png` (from ramdumps/townreturnpotion.p2s, Jul 6):
pill spans x≈208..396 (≈188px), y≈268..290 (≈22px), fixed width, centered on the
item-name row; the name text is wider and overflows both caps.
`ramdumps/_treasureoverflow_shot.png` is a second exhibit.
`ramdumps/townreturnpotion_ee.bin` = decompressed EE RAM (VA == index).

## Draw architecture (all disassembly-verified in pristine SLPM_653.78, fo(va)=va-0x100000+0x80)
- **Core tile draw**: `0x14DCE0(a0=group, a1=tile_id, a2, a3=x, t0=y, t1, t2, t3, stack:
  +0x90=w(s16), +0x98=h(s16), +0xA0/A8/B0=R/G/B, +0xB8=alpha, +0xC0=s8, +0xC8)`.
  Wrapper `0x14DF30` marshals byte/halfword stack args (caller puts w at (sp), h at 8(sp),
  RGB at 0x10/0x18/0x20(sp), alpha 0x28(sp), -1 at 0x30(sp), 100 at 0x38(sp)).
- **Natural-size variant**: `0x14DE30` — calls `0x14D1D0(group, tile)` then reads the tile's
  natural w/h from globals `0x50B284/0x50B286` (struct base `0x50B280`) and tail-calls 0x14DCE0.
  A tile drawn through this path has NO width parameter — its size comes from tile metadata.
- **Tile metadata resolution** (`0x14D1D0`): per-group 4-byte-stride tile entry table
  (base selected by `0x14D020(group)`; groups 1 and 2 share a base; group 0 base at 0x4Cxxxx),
  entry byte[0] → index via `0x14D0D0(byte, lw(0x4B5258 + group*40))`, then a
  handle table (`0x14CF60()` base, 12-byte entries, +4 = handle) resolved by
  `0x492A70`/`0x492700` to a loaded-resource pointer, then `0x490E00(0x50B280, res_ptr,
  u16 entry[+2]=record_idx)` parses the record.
- **Geometry record format**: parser `0x490D20` reads 5 fields (u, v, w, h, page) via the
  generic accessor `0x3A2D10(res_ptr, 5, rec_idx, field_idx)` = **BE u32 at res+8 +
  (rec*5+field)*4**; record count = BE u32 at res+4 (`0x3A2CD0`). Bulk-parse variant
  `0x490E70` mallocs count*10 and stores packed LE {u16 u,v,w,h; u8 page; u8 pad} records.

## The pill's geometry records (found in RAM, treasure dump)
Parsed 10-byte-record array in heap at `0xdca192..0xdca1d8` (townreturnpotion_ee.bin):
**seven records w=188 h=24** (matches the pill exactly), v=0,24,48,72,96,120,144,
u alternating 1801/0/1792, page=12 — seven theme/color variants stacked in an atlas column.
NOTE: this array was NOT found on disc in BE-u32, LE-u32, BE-u16, or raw-LE forms —
the disc source is repacked/compressed or the array is generated. Finding the disc source
(which PACKDATA resource) is OPEN. The array sits among many similar UI-geometry records
(array region roughly 0xdca0ac±; walk-back heuristic stopped early, real start unknown).

## Candidate pill draw site (UNCONFIRMED)
`0x170E98..0x170F14`: state-machine block that queries `0x301E90(1, 0xE1)` and picks tile
pair **(185,186)** vs **(187,188)** (theme variants!), stores the second id at struct+0x74,
draws the first via `jal 0x14E960` (wrapper over `0x14E5E0`) with t1=0x15 (21) and NO width
stack arg. Module instance list head at gp-0x6234 = `0x4FEDBC` (gp=0x504FF0) — but the node
followed from there in the treasure dump did not obviously match (inner obj +0x74 read 176,
data looked like bitmaps; interpretation uncertain). Site NOT yet proven to be the pill.
Other 185-immediates checked and ruled out: 0x21FEA4 (FPU arg), 0x279DFC (float compare),
0x305470 (glyph emit), 0x13F688 (chargen banner middle tile — never touch).

## Fix options (in preference order)
1. **Resource-side**: find the disc source of the 188x24 records; widen w (e.g. →260) IF the
   atlas page has blank texels right of each capsule (RENDER THE ATLAS PAGE FROM THE TREASURE
   DUMP'S GS VRAM to check: GS.bin in the .p2s = 509B header + 4MB VRAM; capsules are 7
   stacked 188x24 sprites). If blank margin exists but contains no right cap, ALSO re-ink
   (project has in-place re-ink discipline, cf. tools/patch_r2138.py). Pure data fix, no EXE risk.
2. **EXE-side stretch**: at the (confirmed) pill call site, reroute the natural-size call to a
   width-taking wrapper with w≈260 via a cave. Cave MUST be below VA 0x4B0DCF (battle-arena
   law) and must not add ANY resident data in 0x4B0E00..0x4FDE30.
3. **Suppress the pill** (draw nothing) if widening proves impractical — likely cleaner than
   overflow, one-instruction NOP-out of the draw call once the site is confirmed.

## Constraints (absolute)
- Battle arena 0x4B0E00..0x4FDE30 ships byte-identical to pristine. No new resident data there.
- Do not touch 0x13F688 or the R1188 resource (pristine law). Real-PS2-compatible fixes only.
- Any EXE change: in-place .text below 0x4B0DCF, or the established patch_exe.py cave discipline.
- v179 (build/BUSIN0_EN_v179_banner_fix.iso) is the current baseline; the pill fix must compose
  with it (patch_exe.py accumulator + build_v9.py pipeline, rebuild via
  `python tools/generate_font_atlas.py && python build/build_v9.py && cp ...`).

## Next concrete steps
1. Extract GS VRAM from townreturnpotion.p2s, render page with the capsule column
   (u≈1792..1989 and u≈0..188 columns, v 0..168; page ids 12 — page→VRAM TBP mapping needs
   the TEX0 of the UI atlas; the deswizzle helpers are in tools/psmt4_deswizzle.py).
2. Confirm the pill draw site (breadcrumbs above; or diff which record index the natural-size
   chain resolves for tiles 185/187 per group).
3. Locate the disc source of the geometry records (check type-29 R2138-family and the R2124/
   R1365 UI resources; try the BE-u32 accessor layout INSIDE sub-resources — sub-headers may
   offset the array; also consider that `0x3A2CD0/0x3A2D10` imply a generic "table resource"
   header {u32 magic?, BE u32 count, BE u32 fields...} — grep PACKDATA for BE-u32 count
   patterns with 5-field stride and w/h pairs (188,24)).
4. Implement per fix option order; add a gate test; build a single-variable diag ISO.
