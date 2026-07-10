# Busin 0: Wizardry Alternative Neo - English Fan Translation

## ABSOLUTE RULE: REAL PS2 COMPATIBILITY

**ALL fixes MUST work on real PS2 hardware.** PCSX2 texture replacement is an investigation tool ONLY — NEVER propose it as a solution. The user has stated this repeatedly. Every translation must modify the actual ISO data (PACKDATA resources, EXE patches, font atlases). If a fix only works in PCSX2, it is NOT a fix.

## CRITICAL TESTING INSTRUCTIONS

**NEVER load save states from an older ISO build.** PCSX2 save states (.p2s) contain the FULL 32MB EE RAM including all loaded game resources. Loading a save state from v22 will show v22's data regardless of which ISO is mounted. **Always boot FRESH from the title screen** when testing a new ISO.

**ONLY analyze RECENT save states — sort `.p2s`/`.ps2` by modification date and use the newest (today's / the current build's) unless the user specifically says otherwise.** Because each save embeds the full 32MB EE RAM from when it was captured, a stale save shows OLD resources/EXE regardless of the mounted ISO, and will silently send a recon down a false path (e.g. a "regression" that is really pre-fix data). Before trusting any save for debugging, confirm it matches the build under test (e.g. read a known patched EXE byte in its `eeMemory.bin`). When the user hands over a batch of saves, `find ramdumps build -name '*.p2s' -newermt '<today>'` first and ignore everything older.

**Verify the ISO before testing:** `python verify_iso.py build/BUSIN0_EN_vNN.iso`

## CRITICAL BUILD INSTRUCTIONS

**ALWAYS rebuild AND copy the ISO in ONE command to avoid stale ISOs:**

```bash
python tools/generate_font_atlas.py && python build/build_v9.py && cp build/BUSIN0_EN_v9.iso build/BUSIN0_EN_vNN.iso
```

**NEVER copy the ISO while the build is still running.** The build writes the PACKDATA directory size as its LAST step. Copying mid-build produces a corrupt ISO with truncated PACKDATA.

**NEVER use `PYTHONIOENCODING=utf-8 python` on Windows.** This is Unix syntax and silently fails. Use just `python` instead.

## Build Pipeline (build/build_v9.py)

1. **Step 1**: v2 pipeline (build_full_english_v2.py) — ALL type-01 resources (R34-R49, R2124, R2654)
2. **Step 2**: Fixed-size injection for problem type-01s (R34, R35, R2124, R2654 — flat format). R34 group 0 is a structural table (49-entry u16 list): Step 2 skips it and maps message mi = group gi−1. R35 is type-02 in the manifest but is handled here by Step 2.
3. **Step 3**: R39 equipment injection (inject_r39_v2.py)
4. **Step 3.1**: R39 inline Japanese patch (tools/patch_r39_inline.py)
5. **Step 3.2**: R39 quest UI labels + quest titles (build/inject_r39_quest.py)
6. **Step 3.3**: R39 block-2 spell descriptions (tools/patch_r39_spell_desc.py) — size-changing block-2 rebuild, pristine-diff gate on every byte outside block 2. All 56 records (v159).
7. **Step 3.4**: R39 AA names/descriptions/UI, blocks 3/4/5 (tools/patch_r39_aa.py) — same gated pattern; header-driven offsets so it composes after the block-2 growth (v161).
8. **Step 3.5**: R46/R47 bulletin board (build/inject_r46_r47.py). The renderer centers each post on the widest line counting 0x0000 pads as full cells — R46 injection therefore uses symmetric per-line padding.
9. **Step 3.6/3.7**: **DISABLED in v85** — the old R1188 patchers (patch_r1188_comprehensive.py / patch_r1188_bw256.py; formerly patch_r1188_direct.py) used a layout off by 1008 bytes and corrupted ~150 live glyph cells of the dialogue font (BUG-3: the r/y/V glyph artifacts). R1188 must ship PRISTINE; the build deletes any stale R1188 override.
10. **Step 3.8**: R2100 chargen font atlas (tools/patch_r2100.py)
11. **Step 3.9**: R2138 unified patcher (tools/patch_r2138.py — sub0/4/6/7/25/26/27). sub4 ("Class Reqs" class-change header) is **RE-ENABLED**: strict in-place pixel re-ink, lossless-roundtrip + change-box containment guards, transfer geometry identical to pristine. The old "sub4 OFF / VIF crash" claim is OBSOLETE (the crash was 93 binary type-02s, not this atlas).
12. **Step 4**: Type-2 variable-size injection + Section 1 opcode patching (tools/patch_section1_offsets.py using the tools/sec1_disasm.py BFS disassembler). Resources whose Section 1 fails the BFS walk (e.g. R989/R990/R1034 — binary Section 1) are SKIPPED by inject_and_patch and ship pristine.
13. **Step 5**: R1193 intro narration (tools/patch_r1193_narration.py) — trailing block after the last FFFF, drawn by 23 opcode-0x14 line records
14. **Step 5c**: R1194 ending narration + R1193 short-prologue variant (tools/patch_r1194_narration.py) — rebuilds R1194 group 0's 42 opcode-0x14 line records ([42 EN lines][EN tail][FFFF]); the R1193 10-record short prologue appends its EN lines at Section-2 end so zero existing offsets move (v161).
15. **Step 6**: Merge patched_type2 into packdata_resources
16. **Step 6.1**: JP-residue guard (v142) — reports any translated group whose built bytes are still identical to pristine JP (i.e. a translation that silently failed to land)
17. **Step 6.5**: Pre-rendered UI strips + item DB + names/library: patch_r2124 / r1365 / battle_strips / camp_strips / facility_strips / r2147 / r1370 / r2880 / r2881_ending / r2882_grave, inject_r34_db, then patch_r2654_names → patch_r2654_library → patch_r1892_names (ORDER MATTERS — they compose on the same R2654 output), plus patch_r2655_library_strips (library banners/tabs/footer, v165). Runs AFTER Step 6's stale-override purge and BEFORE Step 7 — this placement is load-bearing (see the comment block in build_v9.py).
18. **Step 7**: Rebuild PACKDATA (rebuild_packdata.py)
19. **Step 8**: Build ISO (copy original, overwrite PACKDATA + directory size)
20. **Step 8.2**: PACKDATA overflow self-heal + gate (see "PACKDATA Overflow" below)
21. **Step 8.4**: Patch EXE (patch_exe.py)
22. **Step 8.5**: Write patched EXE into ISO

Steps 1, 3–3.5, 3.8, 3.9, 7 and 8.4 are exit-code gated: a failed child process aborts the build (v163 hardening — a failed rebuild_packdata or patch_exe can no longer silently ship stale output).

## Key Architecture

### Translation Data
- `data/translate_chunks/chunk_00-09_translated.json` — original batch translations (0-indexed message IDs)
- `data/translate_chunks/chunk_r38_fix.json` — ONLY entries MISSING from originals (DO NOT override originals)
- `data/type2_translated/batch_*.json` — type-2 dialogue (auto-discovered by glob)
- `data/menu_labels.csv` — font tile definitions for R1272 menu/stat labels (LEGACY — nothing renders from the R1272 atlas, see Font Atlases)

### Message Indexing (CRITICAL)
- The v2 pipeline uses **0-indexed FFFF group numbers** (group 0 = first group after offset table)
- Original chunk files (chunk_00-09) use this same 0-indexed scheme
- **NEVER create fix file entries that override original chunk entries** — the originals are correct
- chunk_r38_fix.json should ONLY contain messages MISSING from chunk_00-09

### Font Atlases
- **R1188** (1024x1024 PSMT4, header=3072): The LIVE dialogue/narration font — a 24x24 serif glyph atlas. glyph_id = row*42 + col; ASCII glyphs at char−32. Uploaded VERBATIM from disc to VRAM TBP0=0x3000 as a 512x256 PSMCT32 transfer (proven via GS dump 20260612061701). It MUST ship pristine — see disabled Steps 3.6/3.7 (BUG-3).
- **R1272** (256x512): NOT the main dialogue font. The original resource is a character sprite. No GS-dump-observed scene samples the English atlas written there; the old "menu tile" positions 106-159 now hold a duplicate A-Z and nothing renders from them.
- generate_font_atlas.py MUST be run before build_v9.py

### Known Format Issues
- Type-01 resources have sub-header + offset table — Step 2 CANNOT handle these (corrupts header). Only v2 pipeline handles type-01.
- R38 sidebar/stat labels render via glyph tiles from MSG glyph streams (the old "via R1272" attribution is unverified — v85 GS dumps show no scene sampling the R1272 English atlas)
- R1188 tab labels are composed at runtime from individual glyph cells (NOT pre-rendered sprites)
- Menu struct records (56 bytes each) at EXE 0x3C3000-0x3C5300 have 2 glyph slots per label
- PSMT8 deswizzle: dbw_ct32 = tex_w / 2. PSMT4: varies per resource.
- GS-dump tooling: in PCSX2 GS dump v9 files, VRAM starts at data_start+425 — prior scripts that read from data_start+0 read garbage.
- **EXE data-table placement (SHIPPING fix = v175+ "Option-E" strncpy-span relocation, BOOT-CONFIRMED Jul 8; the v174 ELF-segment design below is SUPERSEDED history; v173 INCOMPLETE; v171 FALSIFIED):** the battle-heap arena is `0x4B0E00..0x4FDE30`. Battle setup streams ~6MB of monster assets into the heap at `0x800000+`; **ANY of our resident DATA in the arena's pristine-zero heap-padding intermittently stalls that DMA → enemyless-camera / missing-monster softlock** (transient, invisible to static dumps — bytes are identical in working AND broken dumps). **v173's "drop R2100" did NOT fix it** — it left the Patch-14 canonical ADV/LSH tables `0x4C7564`/`0x4C7690` (pristine=ZERO there; we filled it), and SirBewm's v173 saves (`ramdumps/issue1_harpy/`) still softlock the harpy (heapA `0x880000` EMPTY). **DECISIVE:** a diagnostic build with `0x4C7564` **zeroed but ALL caves kept** → harpy LOADS → it's the DATA, the 12 executable caves are EXONERATED. But the tables can't be dropped (they're load-bearing font metrics — zeroing them garbles all dialogue/chargen). **v174 FIX: move ALL font tables into a new file-backed ELF segment @VA `0x580000`** — repurpose the spare degenerate PH1 (e_phnum stays 2); 768B blob (`adv`+`leftshift`+`adv2` tables) in the dead ELF section-header tail @file `0x3FDD00` (zero ISO relocation, ends at the 2044-sector bound); **reserve it by bumping the sbrk break word @file `0x3AF6D4`/VA `0x4AF654`: `0x579800`→`0x581000`** (proven the SOLE malloc base — only 4 in-sbrk instructions touch it, monotonic, all 7 EE dumps confirm). Zero the arena copies → arena truly pristine = battle fix; caves read the segment → **R2100 chargen polish RESTORED** (`ADV2`@`0x580200`; `LSH2` aliased to `LSH`@`0x580100`, 4th table deferred = no regression). Single source `build/_reloc_v147_design.py`; gates: `tests/test_optione_arena.py` (Option-E invariants + THE arena law: no patched byte may fill pristine-zero arena padding; replaced the deleted v174-pinned test_exe_extension_* orphans) + L0 `test_cave_semantics.py` (6/6). **Layered safety:** the arena-pristine battle fix is INDEPENDENT of whether the PS2 BIOS maps the formerly-zero-filesz PH1 — worst case (loader ignores it) = garbled fonts but battle STILL fixed; it CANNOT re-break battle. **SUPERSEDED by the shipping Option-E relocation (v175+):** the tables live instead in the freed span of the shrunk `strncpy` @`0x121568` (368B packed @`0x1215B4`: ADV/LSH/ADV2/LSH2; sbrk word stays `0x579800`; PH1 unused, filesz=0 → zero loader uncertainty; original routine proven full-C-strncpy semantics, single-entry). Arena truly pristine. **BOOT-CONFIRMED (Jul 8, v180 fresh boot): harpy battleable; chargen banner/font/gender, narration, dialogue all good.** The v175–v178 chargen white-banner regression was NOT the font relocation — it was the unrelated blind "pill width" patch @`0x13F688` (that immediate is the banner widget's MIDDLE TILE ID 185, drawn as cap/middle/cap 184/185/186 via `jal 0x14DF30`; width is the caller's `s0`). Withdrawn in v179; regression gate `tests/test_banner_widget_pristine.py` pins the widget span + shop tile selector pristine. Post-mortem: `build/BANNER_PROBLEM_HANDOFF.md`. The item-pill widen shipped v180 DATA-ONLY (R2139 sub13 rec2 w 192→256 + R2138 sub27 band re-ink, `tools/patch_pill_widen.py`, gates `tests/test_pill_widen.py`) — **render-UNVERIFIED** (alchemy menu not reached in the Jul 8 session). ~~[FALSIFIED: v171 "arena-sweep/RANK-2 fixes it"; v173 "drop R2100 = fixed" — both incomplete/coincidental on an intermittent bug. ONLY a truly-pristine arena is safe.]~~

#### Type-02 Section 1 script format (v85 recon)
- Section 1 is a **byte-addressed stream of big-endian u16 opcodes** — odd-length opcodes exist, so it cannot be treated as a u16 array.
- Interpreter dispatcher: va 0x002F3230 in SLPM_653.78, with a 193-entry handler table at 0x004C9360. Recovered per-opcode byte-length table: `build/recon_v85/exe-interpreter/opcode_table_v85.json`.
- Section-2 references come ONLY from: opcode 0x04 (u32 off@+2, u32 cnt@+6), opcodes 0x0C/0x0D (u16 idx@+4), and opcode 0x14 name/label refs (u32 off@+6, u32 cnt@+10 — names are glyph prefixes inside groups).
- Jump targets are Section-1-relative and NEVER need remapping.
- Section-1 patching is done by the BFS disassembler `tools/sec1_disasm.py` + `tools/patch_section1_offsets.py`. **Pattern matching must NEVER be reintroduced.**
- **Unwalked code islands (v171):** the BFS walk only reaches statically-followable control flow. Some scene "events" live in Section-1 islands entered ONLY by runtime/indirect dispatch, so their `0x04` DISPLAY_TEXT offsets are never walked and were kept STALE (pristine) after English grew Section 2 → choices rendered as a bare continue-arrow (issue #9: R1200/R1204/R1208/R1210), narration showed the WRONG group's text (the scattered-text family). `patch_section1_offsets.py` pass **a2** now sweeps these, group-anchored, gated by a strict boundary invariant (candidate offset == a group-start AND span-end == a group's 0xFFFF terminator; multi-group spans from group 0 excluded as a binary false-positive). This is NOT pattern matching. `tests/test_stale_display_offsets.py` pins it, and the `tests/_helpers.py` v84-corruption gate was taught to allow exactly those legit island operands.

### Glyph decode discipline (per-resource glyph pages)
Glyph IDs are **per-resource page slots**, NOT global codepoints — the same u16 id renders DIFFERENT characters in different resources. `msg_glyph_map`-style decodes are cross-resource APPROXIMATIONS: useful as search hints, never as proof (e.g. the R1198 nameplate decoding as 無帰前像 that was actually 騎士団長 "Knight Commander"). When identifying or patching text, anchor SEMANTICALLY inside the target resource (neighboring known strings, offset-table structure, in-resource glyph equations) — never via font-atlas cell positions or a borrowed glyph map.

## Translation Status (post-v166 — public beta, effectively complete)

Translated and shipping: all dialogue/narration (R1207 at 912/912 after the v166 fresh-translation wave; R1206 four-segment misalignment repaired), the **entire in-game library — 100%** (R2654 texts/names/blurbs incl. control-token syntax with a token-preservation gate; R2655 banner/tab/footer strips), **R39 complete** (equipment, quests, spell descriptions, AA names/descriptions/UI — the old "in-battle CAST description" open item shipped via Steps 3.3/3.4 in v159–v163), all pre-rendered UI strips (town hub, facilities, battle/camp chrome, status, chargen sidebar — and R2138 sub4 "Class Reqs", RE-ENABLED, see Step 3.9), rosters + nameplates, EXE SJIS (all player-visible strings; remaining ~686 runs are debug-only), intro + ending narration.

**Remaining (small pool):**
- **Equipment type icons** (剣/斧/杖 category glyphs; identified as R2156 — id from the Jul-2 recon, not independently re-verified) — CAPTURE-GATED: no screenshot yet confirms JP vs EN. Do not patch blind.
- **Credits / staff roll** — likely a burnt-in FMV stream outside PACKDATA. Capture-gated.
- **Ending render verification** — R2881 sub7 / R2882 / R1194 ending narration are translated, but no ending GS dump or screenshot confirms the on-screen render yet.
- **Minor cosmetic offsets** (beta reports welcome): battle "Target" label, L1/R1 bottom-bar hints, treasure-drop name placement.

**Laid to rest — do NOT re-chase:** the "~587 unscanned type-2 resources" fear (Jul-2 audit: loose rescan of all 617 → R680–R911 is binary noise; the only real loss was the md_import batch, recovered in the v161 wave); dungeon compass / automap HUD (nonexistent — hand-mapping crawler); title boot menu (natively English); R1188 tab labels (render via R2138 sub7, English since v8x).

### PACKDATA Overflow — SELF-HEALED by Step 8.2 (do not re-chase)
The rebuilt PACKDATA.DIG outgrows its original slot and would overrun the next file (BSN2_0.DSI, audio). Step 8.2 self-heals at ISO build time: it parses the root directory by name, relocates the following file upward by the needed shift (dynamic — not a fixed offset; ISO extended, PVD volume size updated), and a build-gate assert verifies the relocated file's first sector no longer collides with PACKDATA's end. verify_iso MD5-checks the relocated file. **Overflow is NORMAL, not corruption — never assert overflow==0.** Growth tripwire: `tests/_helpers.py PACKDATA_OVERFLOW_BUDGET_SECTORS = 320` (raised from 256 on 2026-07-04 after the v163–v165 library waves legitimately grew R2654). The relocation machinery is uncapped; the budget exists purely so unexplained growth trips a test — if it trips, account for the delta before bumping.

## Target Disc
- **SLPM-65378** — original release, software **v1.03** (NOT Atlus Best Collection SLPM-65876, which is **v2.01**). Some SLPM-65378 dumps are mislabeled "(v2.01)" in the filename — the MD5 (48a5639afdf9931913c7dde298dc5349) is authoritative, not the filename.
- trap15 has an active parallel project targeting SLPM-65876.
- **Atlus Best (SLPM-65876, v2.01) is the "bug-fix version"** — it reportedly fixes NATIVE post-battle freezes (notably floor-4 / after Soul Crush counterattacks) present in the v1.03 original. This is a SEPARATE bug class from our font-tables-in-arena softlock (Option-E, boot-confirmed fixed): a native v1.03 freeze could still exist on our target and would need level-4+ save states to diagnose. Do NOT conflate the two.
