# FULL PROJECT AUDIT — 2026-07-02 (v158 era)

Seven parallel read-only recons: EXE patch stack, build pipeline, translation data,
test suite, docs/repo hygiene, content completeness, untranslated names (from
ramdumps/fuckingthisguyman.p2s, verified to be a genuine v158 dump).
Nothing was modified. Raw agent evidence/scripts live in the session scratchpad
(`scratchpad/audit1..7/`). Findings are deduplicated and ranked.

---

## CRITICAL — fix before the next build ships

**C1. 447 finished translations are silently dropped from every build.**
`data/type2_translated/batch_md_import.json` uses key `"message"`; `build/build_v9.py`
(~line 584) reads `e['msg_index']` and the per-file `except` swallows the KeyError
(proof: `build/last_build_log.txt:1263`; built `1203_type02.raw` M68 still pristine JP).
399 of the 447 exist in no other batch (shop/bar/NPC one-liners, R1196–R1213/R1352–57).
⚠ DO NOT just rename the key: the 7 entries overlapping other batches carry DIFFERENT
text for the same index — the batch appears to use a different indexing scheme and
needs re-alignment before re-keying.

**C2. The ISO-level test tier has been silently disabled since v85.**
`tests/_helpers.py:126` defaults to `build/BUSIN0_EN_v85.iso` (long deleted) → all 8
"skips" in every green run are the R1188-pristine (BUG-3), binary-VIF crash, and
PACKDATA/BSN2 audio-overflow gates never running. All 8 PASS when pointed at v158
(verified) — the net just wasn't in the water. Fix: adopt
`test_line_width._newest_iso()` (globs `BUSIN0_EN_v*.iso`, newest) into `_helpers`,
and make "ISO tier skipped" a failure for release runs.

**C3. build_v9.py ignores child exit codes at the most dangerous steps.**
Step 7 (`rebuild_packdata.py`, `os.system` rc unchecked — a mid-write failure leaves a
truncated TOC-less DIG that Step 8 embeds), Step 8.4 (`patch_exe.py` rc unchecked — a
hard-fail ships the PREVIOUS build's patched EXE, or the JP EXE if none), Step 1 and
Steps 3.5/3.8/3.9 likewise. Steps 3/3.1/3.2/3.3/6.5 already have the correct
check-and-exit pattern — apply it everywhere; write outputs to temp names + `os.replace`.

---

## HIGH

**H1. R39 has 168 residual JP groups in the built file** (517 pristine → 168): 3 spell
CAST effect descriptions (M210–212) + ~165 AA/technique names (M224–263+). This IS the
open "in-battle CAST description" item — real, resource-identified, not a stale
screenshot. Injection route exists (chunk/sysmsgs fix files). Plus tiny system-message
stragglers: R43 ×3, R47 ×4, R46 ×1.

**H2. Untranslated names (from the live v158 dump + corpus sweep).**
- Screenshot nameplate = R1198 opcode-0x14 label, glyphs (483,494,510,404) = 騎士団長
  "Knight Commander". Its msg_glyph_map decode (`無帰前像`) has no `data/name_labels.json`
  key → `patch_section1_offsets.py` safe-fallback ships JP. Fix = add the key; same
  route for 12 more nameplate keys (~40 occurrences, R1196–R1213; table in the recon).
- LIKELY LIVE MISTRANSLATION: `無帰前` = glyphs 騎士団 "Knights" ships as **"Adventurer"
  ×19** in R1196/97/1203/07/1355 (glyph identity proven from the nameplate). Verify in-game.
- Rosters: R1892 party bar still katakana for Yoppen/Lidi/Turgot/Belgrano/Bertin/Weil
  (allowed-set gate + missing kana-grid entries + Belgrano exceeds the 16-byte field);
  R2654 sub7 ~23 katakana names (visibility unconfirmed).
- ~283 unmapped 0x14 text lines (chants, ghost voices, hiragana class names) are a
  separate uncovered surface.

**H3. Falsified docs still point future sessions at dead ends.**
`data/chargen_spacing_backlog.md` + `build/_chargen_backlog.md` assert Patch 19 is the
shipped path and declare the R2100-font theory "DISPROVEN" — both falsified (v133 dead
path; v158 proved R2100 correct). `HANDOFF_chargen_text.md` §1/§2/§5/§8 obsolete.
`HANDOFF_box_request_formatting.md` §1/§4/§5 superseded. `data/text_restructure_roadmap.md`
line ~71 carries the wrong-way "correction". CLAUDE.md: overflow warning stale (Step 8.2
self-heals with gates), R2138 sub4 claim FALSE (re-enabled in tree since c15bdaa),
pipeline list missing Steps 3.3/6.1/6.5/8.2. Banner or rewrite these.

**H4. The entire v158 fix is uncommitted** (372 untracked files incl.
`data/r2100_ascii_metrics.json`, which `tools/glyph_metrics.py` now requires — a fresh
clone cannot build). Proposed commit 1: the v158 code+data+tests set; then docs; then a
gitignore hygiene pass (root `_*`, `build/_*`, `build/recon_*`, shard files, stackdump).

---

## MEDIUM

- **M1.** Intro double-definition: `batch_intro.json` vs `batch_intro_narration.json`
  both define r1193/g0 + r1194/g0 with different text; winner decided by glob order.
- **M2.** Orphaned-but-loaded-looking data: `chunk_md_import.json` (976 would-be
  overrides), `chunk_r38_fix_no_gender.json`, `.bak` — archive so no future glob
  resurrects them. Cross-fix conflict r43/m26 needs a human pick.
- **M3.** Patch 13 site 1 is silently overwritten by Patch 14's delay-slot nop —
  correct behavior, lying build log, source-order load-bearing. Document or drop the tuple.
- **M4.** Diagnostic caves (FIRE_DIAG @0x4C7410 — a PROVEN-stomped address — and
  CHARGEN_DIAG @0x4C7790) bypass `assert_install_safe`; a future diag session could
  produce corrupted evidence. Relocate below 0x4B0DCF.
- **M5.** Patch 19 ships live hooks + 116B caves for a proven-dead path and still reads
  the R1188 tables (would resurrect "Ge nde r" if the path ever woke). Retire or retarget.
- **M6.** `build/BUSIN0_EN.iso` (Step-1 side product, NO overflow relocation) is a
  ship-the-wrong-file trap; gate it off or rename `.DO_NOT_SHIP`.
- **M7.** Overflow budget headroom: 237 of 256 sectors used — 19 sectors (~39KB) until
  `test_packdata_overflow` fails. Raise deliberately or plan shrink.
- **M8.** verify_iso coverage gaps: no R1188-in-ISO, R39, R2138, R2100, v158 tables, or
  full-EXE-hash checks; the 2 by-design gender FAILs print "SOME CHECKS FAILED" on every
  good build (alarm fatigue). Add a KNOWN_FAIL allowlist + build-id stamp.
- **M9.** mtime-based freshness skips (choice_groups/v86_strips/line_width/narration_wrap)
  can permanently disable ISO comparisons; suite still brands itself "v85 REGRESSION SUITE".
- **M10.** 8 hardcoded `C:/Programmieren/...` paths (one lowercase variant) + silent
  TTF→default-font fallbacks in 8 patchers; atlas staleness never checked.
- **M11.** Test coverage gaps: EXE SJIS patches, Patch 6/24 built-EXE bytes, R47 built
  output, R2138 per-sub containment (incl. a sub4 guard), name pipeline patchers.
- **M12.** Memory hygiene: `project_font_systems.md` (R1272 "FULLY WORKING" — falsified),
  `project_stat_label_hunt_status.md` ("mystery persists" — solved by R2138),
  `project_chargen_elements.md` stale; one MEMORY.md mislink (Patch-27 entry → wrong file).

## LOW

7 literal `\n` in chunk_08 (rendered as space — authored break lost); `batch_gap1347` g5
leading ' / '; r48/r2654 two over-width UI lines; unreachable "already patched" branches;
stale FIRE_DIAG prints; duplicate superseded constants + v147 narrative in
`_reloc_v147_design.py`; Patch 8 lacks a pristine check; root clutter list (see docs recon).

## CLEAN BILLS OF HEALTH

- v158 patch stack: 115/115 byte-checks attributable, no stowaways, SELFCHECK PASS.
- chunk_r38_fix override rule: 0 collisions. Encodability: effectively perfect.
- Leftover JP inside translated strings: 0. Test registration 35/35, real teeth.
- Type-2 hidden-dialogue fear laid to rest: loose rescan of all 617 → R680–911 is all
  binary noise; the only real losses are the md_import batch (C1).
- EXE SJIS "debug-only" claim survived spot-check. Title boot menu natively English.
- R2138 sub4 already FIXED in tree — ships with the next build.

## SUGGESTED ORDER OF WORK

1. C3 exit-code/atomic-write hardening, then C2 test re-arm (both tiny, protect everything else).
2. C1 md_import re-alignment (biggest content win: ~400 lines).
3. H2 name_labels additions + "Adventurer"→"Knights" verification + roster patcher extensions.
4. H1 R39 CAST descriptions + AA names; R43/R46/R47 stragglers.
5. H4 commit v158 + H3 doc banners (one sitting).
6. M-items opportunistically; R2654 library bulk (1077 groups) after confirming visibility.
