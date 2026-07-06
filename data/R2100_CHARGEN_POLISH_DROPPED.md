# R2100 chargen-font polish — DROPPED in the battle fix (restore target)

**Why dropped:** the R2100 ADV2/LSH2 chargen font-metric tables (95–256B) placed *anywhere in the
battle-heap arena* (0x4B0E00..0x4FDE30) intermittently stall the ~6MB monster-model asset DMA →
enemyless-camera softlock. PROVEN at BOTH placements: 0x4B1000 (v158/v173, dump Emptyfuckyou) and
0x4C785F (RANK-2, dump mfs). The pristine EXE (no R2100 tables) is the only config that works
(user A/B: Theabsoluteculprit.p2s). Below-arena has 0 free bytes; the libgraph block black-screens.
So the tables had nowhere safe to live → removed. Chargen reverts to the mild pre-v158 "Ge nde r"
uneven spacing (caves now read the canonical R1188 tables @0x4C7564/0x4C7690).

## What the R2100 patch ACHIEVED (the polish we want back)
- Chargen / request-screen text used the **R2100 UPRIGHT font metrics** (proper per-glyph advance +
  left-shift) instead of the R1188 oblique/dialogue metrics, fixing the "Ge nde r" / "In t" uneven
  letter spacing on the Name/Gender/Race/Class/personality screens.
- Delivered via 4 caves reading two 256B tables: ADV2 (advance) + LSH2 (left-shift), gid 0..94.
  Readers: P26 + P27 (ADV2), P29 + P31 (LSH2). Tables built by tools/glyph_metrics.adv2_table_256()
  / leftshift2_table_256(). Root cause + tables are ACCURATE (0/95 diff vs VRAM, per the chargen
  root-cause memory) — the DATA is correct; only the PLACEMENT is the problem.

## How to RESTORE it safely (EXE-extension project)
The tables need a home OUTSIDE every runtime-used region (image, arena-heap, stack, libgraph). The
only such space is a **new file-backed LOAD segment appended to the ELF** at a genuinely-unused VA.
Put ADV2/LSH2 (and, ideally, the migrated caves) there, repoint the 4 cave reads to it, done — the
polish returns with zero arena footprint. See the exe-extension run (runs/CLAUDE-RUNS) for the
feasibility + migration design. The caves themselves are EXONERATED (present in every working dump);
only our added arena DATA was ever the battle culprit.

## Exact revert-to-restore
Reading tables from a new-segment VA X: build_p26/p27 read X_adv, build_p29/p31 read X_lsh; install
adv2_table_256()/leftshift2_table_256() at X (256B each). Positive lbu offset => lui = (X>>16)+carry
(mind the sign-extension — the L0 gate tests/test_cave_semantics.py catches it). Everything else is
already in place.
