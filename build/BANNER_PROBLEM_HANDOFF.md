# Chargen white-banner regression — full handoff

## ✅ SOLVED + **BOOT-CONFIRMED** (2026-07-08 evening, v180 fresh boot: chargen banner BACK,
## font spacing + gender tiles still correct; narration/dialogue also verified good)
## Root cause was the "item-pill" patch @0x13F688. Regression gate: tests/test_banner_widget_pristine.py
The Option-E diff item dismissed as "unrelated" was the cause. `addiu a1,zero,185`
at VA `0x13F688` is **not a pixel width** — it is the **middle-segment TILE ID** of a
3-part stretchable box widget. The function makes three `jal 0x14DF30` draw calls
with `a1 = 0xB8 / 0xB9 / 0xBA` (184 = left cap, 185 = middle, 186 = right cap); the
real width is the caller-computed `s0` passed on the stack (`sd s0,(sp)`), and the
middle call is skipped when `s0 <= 0` (`blez` at 0x13F654). The blind "pill width
185→440" patch made the middle segment reference tile 440 → the white middle strip
vanished while both caps kept drawing — exactly the screenshots. RAM-verified:
`0x13F688` = imm 185 in `168gender_ee.bin` (banner present), imm 440 in
`177gender_ee.bin` **and** `stillborked_ee.bin` (banner absent) — the pill patch was
outside the `DISABLE_P27_P14` lever, which is why the caves-off v178 diag still broke.
Fix: patch withdrawn in `build/patch_exe.py` (site now ships pristine); the item-name
spill must be fixed via the caller's `s0` width computation instead.
Also verified along the way: pristine EXE truly is all-zero at `0x4C7564/0x4C7690/`
`0x4B1000/0x4B1100` (rule-out #2 now proven), the original `0x121568` routine is
full-semantics C strncpy incl. zero-padding tail (rule-out #3 strengthened), and
R38's control-token structure is byte-identical v168↔v176 (only glyph text differs).
Shipped as `build/BUSIN0_EN_v179_banner_fix.iso` — one boot to confirm.

## The bug in one sentence
On the character-creation screens, the **white section-banner** (the horizontal scroll at the bottom that holds the description text — "Gender sets base stats…", "Human: High faith…") **fails to draw** in every Option-E build, but draws correctly in v168. When it's absent, a stock cursive decorative word ("Personality") that the banner normally covers is left exposed over the character art. Everything else on the screen (font spacing, gender ♂/♀ symbols, race list, portraits, top prompt) is fine.

## What you must NOT break while fixing this
- **Battle fix** (the whole reason for the Option-E work): the EE battle-heap arena `0x4B0E00..0x4FDE30` must ship byte-identical to pristine (no resident data in its pristine-zero heap-padding), and the shrunk `strncpy` @`0x121568` must stay. This is confirmed working on real hardware (the "harpy" fight loads). Any banner fix must keep it.
- **Font fix** (Option-E): chargen text spacing is now correct; don't regress it.
- **Gender fix** (v176): ♂/♀ tiles sit correctly; don't regress it.
- Real PS2 target (SLPM-65378). PCSX2 is an investigation tool only.

## Build timeline
- **v168** = last known-good chargen. Font metric tables live IN the battle arena: R1188 ADV @`0x4C7564`, LSH @`0x4C7690`; R2100 ADV2 @`0x4B1000`, LSH2 @`0x4B1100`. Banner works. **But battle softlocks** (our tables in the arena stall monster DMA).
- **v173/174/175 "Option-E"** = battle fix. Moved all font tables OUT of the arena into the freed `strncpy` span, zeroed the old arena sites, rewired the readers. Battle fixed; **banner broke.**
- **v176** = + gender-tile guard (fixes an unrelated fling). **v177** = v176 + Patch 6 disabled. **v178** = Option-E + all chargen text caves disabled (diagnostic).

### Exactly what Option-E changed vs v168 (full EXE diff)
1. **Font tables relocated** into the freed `strncpy` span, packed 4×92 bytes = 368B exactly: ADV `0x1215B4`, LSH `0x121610`, ADV2 `0x12166C`, LSH2 `0x1216C8`. (Values byte-identical to v168's tables, just moved.)
2. **`strncpy` @`0x121568` shrunk** 444B → 76B replacement; the freed tail `0x1215B4..0x121724` now holds the tables (was strncpy's MMI code).
3. **Old arena table sites zeroed**: `0x4C7564`, `0x4C7690`, `0x4B1000`, `0x4B1100` (256B each) → all zero.
4. **6 font caves rewired/relocated** (below-arena .text pads): at `0x4AB5xx`, `0x4AFAxx`, `0x4B04xx`, `0x4B0Cxx`.
5. **Item-pill patch** `0x13F688` (treasure-drop cosmetic, unrelated).
6. **22 PACKDATA resources differ** — all text/dialogue/library content (translation waves). Includes R38 trait text ("High faith"→"Low faith", "wise"→"hardy"). **The chargen sprite resources R2138 / R2100 / R1370 are byte-identical to v168** (verified by a full PACKDATA MD5 diff).

## Evidence: the save states (PCSX2 .p2s; EE RAM: VA == index)
| file | build | banner |
|---|---|---|
| `build/168gender.p2s`, `build/168race.p2s` | **real v168** (0x4C7564 populated with `090b0e14…`) | **PRESENT** |
| `ramdumps/177gender.p2s`, `ramdumps/177race.p2s` | v177 (Option-E, Patch6 OFF, gender guard) | **absent** |
| `ramdumps/bigasswhambam.p2s` | v175 Option-E (no gender guard) | absent |
| `ramdumps/stillborked.p2s` | **v178 diag (ALL chargen caves off)** | **absent** |

Screenshots extracted to `ramdumps/<name>.png`; decompressed EE RAM to `ramdumps/<name>_ee.bin`. So the regression is **build-dependent, not state/timing** (v168 present 2/2; Option-E absent 4/4 across two screens and three builds).

## CONFIRMED
- Banner regression is build-dependent (above).
- Gender guard (v176) works on a real boot (177 saves show ♂/♀ correct).
- Banner draw-code AND banner sprite resources are byte-identical v168↔Option-E.

## RULED OUT (with the proof — don't re-chase these)
1. **Patch 6 (the mode-5 RenderAllTiles skip @JAL `0x2F2568` → trampoline `0x4B0D4C`).** v177 has Patch 6 OFF and the banner is *still* gone; v168 has Patch 6 ON and the banner is *present*. So the banner is independent of Patch 6, and is **NOT a RenderAllTiles tile** (running the tile pass does not draw it). The earlier "Patch 6 eats the banner" recon was WRONG.
2. **Zeroing the old sites `0x4C7564`/`0x4B1000`.** Pristine EXE has those addresses = all zero, and the pristine game shows the banner (standard UI). So Option-E (zeroed) == pristine there. *(Caveat: "pristine has the banner" is assumed from it being a stock UI element — NOT independently verified. See open questions.)*
3. **The `strncpy` shrink.** `0x121568` is single-entry: all 12 `JAL`s in the EXE target `0x121568`; there is exactly one `jr ra` at `0x12171C`; `0x1215B4..0x121724` is strncpy's own MMI/SIMD fast-path (op 0x1C/0x1E/0x38 vector ops); **nothing in the entire EXE jumps/calls into the freed span.** Replacement proven equivalent by `tests/test_shrink_equivalence.py` (dual-oracle, 2008 cases). **GAP: the test only exercised the scalar path + a C-strncpy oracle; it never ran the ORIGINAL's MMI fast path.** Also unverified that `0x121568` is semantically `strncpy` (vs some other string routine).
4. **A missed table reader.** Every EA-scan hit into the zeroed sites / freed span turned out to be a struct field at a combined offset off a pointer or jal-return register (VA `0x133B94` = `lw 0x1054(v0)` v0=jal-return; `0x1899E0`/`0x189E60` = `lbu 0x1674(at)` after `lui at,0x1` = offset `0x11674`; `0x423320`=`lw 0x1000(a1)`; `0x461770`=`lw 0x1100(s2)` in COP1 code). The 8 real font-cave readers are all correctly repointed to the new tables.
5. **The chargen text caves (Patch 14/19/26/27/29/31).** `build/BUSIN0_EN_v178_diag_nocaves.iso` builds Option-E with `DISABLE_P27_P14=1` → all six skipped (confirmed in build log AND in `stillborked_ee.bin`: P29 pad `0x4B0C48` = 0). Banner **still gone.** So the caves are exonerated.

## The uncomfortable core fact
The v178 diag has the caves OFF but **still keeps** the strncpy-shrink, the tables @`0x1215B4`, the zeroed sites, and the resource diffs — and the banner is still gone. Since strncpy / zeroed-sites / readers are "ruled out" (with the caveats above) and the caves are now ruled out, the cause is either:
- one of my rule-outs is **wrong** (most suspicious: the strncpy MMI-path gap, or the unverified "pristine has the banner" assumption), or
- the **tables @`0x1215B4`** matter via a path nobody has found (though nothing reads or executes that span), or
- a **resource diff** matters (though the sprite resources are identical), or
- **something not yet examined.**

## Biggest gap / where I'd start
**Nobody has located the code that actually draws the white banner sprite.** Find it. Two concrete ways:
- **GS/GIF display-list diff**: `168gender_ee.bin` (banner present) vs `stillborked_ee.bin` (absent). Find the draw primitive / texture for the white scroll in one and confirm it's missing or malformed in the other. That localizes the trigger to a specific draw call and its inputs.
- **VRAM compare**: is the banner *texture* uploaded to GS VRAM in the v168 dump but not the Option-E dump? If the texture upload is missing, the problem is upstream (a setup/DMA path), not the draw.

## Other open questions
- **Verify pristine actually has the banner.** If pristine (untouched JP) does NOT render this banner, then the banner is tied to OUR work (a resource or patch) and the whole framing flips. `build/_v168_ref.iso` is a reconstructed v168 you can boot; a truly pristine JP boot would settle it.
- **Re-test `strncpy`:** run the ORIGINAL 444B routine's MMI fast path against the replacement; confirm `0x121568` is semantically strncpy.
- **Enumerate the 22 differing resources** and check each for any chargen/banner relevance (not just the three known-identical sprite resources).

## Technical reference
- **Read a save's EE RAM**: it's a zip; `eeMemory.bin` is zstd-compressed. `VA == index` in the decompressed buffer. (See any of the `ramdumps/*_ee.bin` extraction one-liners in the shell history, or reuse this: open zip, read `eeMemory.bin` member, zstd-decompress.)
- **VA → EXE file offset**: `fo(va) = va - 0x100000 + 0x80`. Pristine EXE: `extracted/SLPM_653.78`. Reconstructed v168: `build/_v168_ref.iso` (extract `SLPM_653.78` via the ISO PVD/TOC).
- **Key addresses**: mode global `0x4FED18` (chargen=5); gp `0x504FF0`; RenderAllTiles `0x30B840` (32-slot loop, 50B records at `*(0x4FE70C)`, 679-entry descriptor table at `*(0x4FE708)`); chargen renderers `0x3A2EF0` (box text) / `0x307510` (body text); gender tiles id `0x2A0`/`0x2A1`.
- **Build**: `python build/build_v9.py` (then it writes `build/BUSIN0_EN_v9.iso`). Diagnostic env levers in `build/patch_exe.py`: `DISABLE_PATCH6`, `DISABLE_P27_P14` (drops P14/19/26/27/29/31), `CHARGEN_DIAG`, `FIRE_DIAG`. Single-source relocation design: `build/_reloc_v147_design.py`. Gates: `python verify_iso.py <iso>`, `python tests/run_all.py`, `python tests/test_cave_semantics.py`. Cave disassembler: `tools/mips_cave_analyzer.py`.
- **Built ISOs on disk**: `BUSIN0_EN_v176_gender.iso` (md5 `f3db1f1b711baaa090ae8db27e748b2b`, = default build), `BUSIN0_EN_v177_banner.iso` (`68c70a60…`, Patch6 off), `BUSIN0_EN_v178_diag_nocaves.iso` (`cde57460…`, caves off), `_v168_ref.iso` (reconstructed v168).

## Deliverable wanted
The user is at work and wants **bootable diagnostic options ready when home** — builds that bisect the remaining Option-E changes so a single boot each isolates the cause. Prime candidates to prepare: (a) revert the `strncpy` shrink / keep the region as real code; (b) leave the old sites populated instead of zeroed (battle-unsafe, diagnostic only); (c) a pristine-font build (no font patches) on the battle fix. Because the banner can't be seen statically, each diagnostic needs one boot to read — so make each one flip exactly one variable.
