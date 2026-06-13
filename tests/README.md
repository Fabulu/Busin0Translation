# v85 Regression Test Suite

Locks in the v85 bug fixes so future changes cannot silently reintroduce the
v84 bug classes (Section-1 scene-script corruption, R1188 dialogue-font
corruption, bulletin-board layout, R39 quest tables, R1193 narration).

## RULE

**`python tests/run_all.py` must report 0 FAILED before any ISO is handed to
the user.** For a release candidate, all three tiers must actually run (no
SKIPs): build outputs present in `build/patched_type2` /
`build/packdata_resources` and the ISO at `build/BUSIN0_EN_v85.iso` (or
`$BUSIN_ISO`).

## How to run

```bash
python tests/run_all.py          # whole suite, summary table, exit != 0 on FAIL
python tests/test_sec1_disasm.py # every module is also standalone-runnable
BUSIN_ISO=build/BUSIN0_EN_v86.iso python tests/run_all.py   # test another ISO
```

No pytest needed (plain stdlib). The whole suite runs in ~1 second. Tests
never modify repo files — synthetic builds go to `tempfile` directories.

## The three tiers

| Tier | Inputs | Behavior when absent |
|------|--------|----------------------|
| 1 | `extracted/packdata_raw/` pristine extracts + source/data files | SKIP (never FAIL) |
| 2 | build outputs: `build/patched_type2/*.raw`, `build/packdata_resources/` | SKIP |
| 3 | a built ISO (`$BUSIN_ISO`, default `build/BUSIN0_EN_v85.iso`) | SKIP |

Tier 1 always runs and needs no build. Tier 2 validates the artifacts of the
last `build/build_v9.py` run. Tier 3 extracts resources straight from the
ISO's PACKDATA.DIG (TOC located via the ISO9660 root directory).

## What each module guards

| Module | Tier | Guards |
|--------|------|--------|
| `test_sec1_disasm.py` | 1 | BFS disassembler walks pristine R1196/R1197/R1198/R1193 with 0 invalid opcodes and sane instruction counts; the ground-truth FFFF-end invariant on every pristine `0x04 cnt>0`; garbage streams fail cleanly; R989/R990/R1034 (binary VIF data) FAIL the walk so the skip-on-failure net protects them. |
| `test_patch_section1.py` | 1+2 | `inject_and_patch()` on R1198 with synthetic text: re-walk OK, FFFF invariant, Section-1 diffs confined to walked operand ranges (`0x04` pc+2..9, `0x0C/0x0D` pc+4..5, `0x14` pc+6..13); R989 fallback returns `(None, 'sec1 walk failed...')` and writes nothing. Tier 2: the same three assertions on EVERY `build/patched_type2/*.raw` — **the v84 corruption fails this gate instantly**. |
| `test_pipeline_rules.py` | 1+2 | Static source guards: R1188 patchers (Steps 3.6/3.7) stay disabled in `build_v9.py`; no `MULTI_WORD_OPCODES`/`body_positions` pattern matching ever returns to `tools/patch_section1_offsets.py`; R34 `mi = gi - 1` mapping + group-0 table skip present; `patched_type2` purge present. Tier 2: `1188_type01.raw` ABSENT from `build/packdata_resources` (pristine fallback). |
| `test_r46_board.py` | 1+2 | BUG-8/9: `build_symmetric_payload` on synthetic messages (capacity exactly filled, FFFE count preserved, no dangling FFFE, uniform leading pad, width cap). Tier 2: built R46 byte length + per-sub FFFF counts == pristine; sub0 msg 21 decodes containing `i'll never forget`. Functions are AST-extracted from the injector so importing it does not run the build. |
| `test_r39_quests.py` | 2 | BUG-7: G353 description in English with `500G`; G388 == `Mayor of Duhan`; all non-zero slots of offset tables G346/G381/G411/G442 resolve to the same (group, glyph ordinal) as pristine; group count unchanged; file <= 16 sectors. |
| `test_r1193_narration.py` | 1 | BUG-10: `build_r1193` into a temp dir produces exactly 23 trailing `0x14` line records in pages 4/3/2/4/1/3/2/3/1 tiling the trailing block; every line <= 23 glyphs, control-code free, decodes to English; deterministic (two runs byte-identical); `sec2_size` header consistent; output Section 1 re-walks. |
| `test_iso_level.py` | 3 | BUG-3 gate: R1188 in the ISO byte-identical to pristine; R1196 from the ISO walks + FFFF invariant; R2100/R2138 NOT pristine (chargen English still ships); R989/R990/R1034 byte-identical to pristine (VIF-crash class). |

## Shared infrastructure

`tests/_helpers.py`: test runner (PASS/FAIL/SKIP, nonzero exit on FAIL),
PACKDATA TOC parsing + ISO extraction, type-02 header/Section-2 parsing,
FFFF group splitting, glyph decoding via `data/english_glyph_table.json`,
Section-1 walking via `tools/sec1_disasm.py`, and
`sec1_regression_check()` — the shared three-assertion v84-bug-class gate.

Verified to detect simulated v84-class corruption: a single byte flipped
outside walked operand ranges, and a DISPLAY_TEXT count that no longer ends
on a 0xFFFF terminator, both fail the gate.
