# RECON 5 — NPC Nameplate Coverage Audit

## HEADLINE
The "13 missing keys / 無帰前='Knights' ships as 'Adventurer' x19" gap in MEMORY is
**ALREADY RESOLVED** by the badge-kanji glyph relabel (data/msg_glyph_map.json, Jul 4)
+ name_labels.json re-derivation (Jul 5). The MEMORY note and the two build/ report
JSONs that seeded it are **STALE** (generated Jun 25/27, before the fix).

A fresh read-only re-scan of the live decode path (current msg_glyph_map +
name_labels, over R1190–R1360, the nameplate family) shows **zero unmapped NPC
nameplates and no harmful collapse.**

## (a) MISSING KEYS
Only these nameplate islands decode-but-don't-map now — none are NPC names:
- `０１２３４５６７８９−` x104, `０００` x11, `５`/`１` — numeric HP/stat bar strings
  (correctly left verbatim; not names).
- `かつて` x1 (R1193) — a narration fragment; R1193 lines are owned by
  patch_r1193_narration.py, not this map.

So the true missing-NPC-key count is **0**. The ~13 "missing" keys from the stale
report were the 無帰-glyph decodes (無帰前像 / 無帰ルッツ / ドラクル無帰前 / 無帰 …) that the
Jul-4 badge-kanji relabel turned into 騎士団長 / 騎士ルッツ / ドラクル騎士団 / 騎士団 — all now
present in name_labels.json.

## (b) FALLBACK MECHANISM
Path: tools/patch_section1_offsets.py `inject_and_patch()` (build Step 4).
- A nameplate = a 0x14 NAME/LABEL prefix at the head of a translated Section-2 group.
- Line 764-771: decode the JP glyph slice via msg_glyph_map (`_decode_jp`), look up
  `_NAME_LABELS.get(jp)`. **If found → write English; if MISSING → `glyphs =
  list(old_slice)` = keep the original JP glyphs verbatim.**
- There is **NO generic "Adventurer"/"Knights" default.** A missing key renders as
  Japanese, not as a wrong English label.
- (A group is only touched at all if it has a msg_translation entry; otherwise the
  whole group, name included, ships pristine JP.)

The old "Adventurer x19" was NOT a fallback default — it was the GLOBAL glyph map
mis-decoding the badge kanji 騎士団 to 授士 (=Adventurer), which name_labels then mapped.
Fixing the glyph map fixed the decode; 授士→Adventurer now legitimately hits only x3.

## (c) COLLAPSE COUNTS (current decode)
- **No distinct NPCs collapse onto one wrong nameplate.** Almost every English value
  maps from exactly ONE distinct JP key.
- `Knights` x19 all come from the SAME single JP key 騎士団 (the knight ORDER), spread
  over R1196/1197/1203/1207/1355 — a faithful recurring role label, not a collapse.
- Knight FAMILY is fully disambiguated into distinct keys:
  騎士団→Knights(19), 士騎戦→Knight(12), 騎士団長→Commander(1, R1198),
  騎士ルッツ→Knight Lutz(1, R1204), ドラクル騎士団→Dracul Knights(1, R1210),
  女騎士→Lady Knight, 個騎士→Paladin, 扱騎士→Dark Knight, 授士→Adventurer(3).
- Only multi-key value is `Orc` x18 from オーク(17) + 図くオーク(1) — both legitimately Orc.

## (d) RESIDUAL RISK behind the user's "repeated Knights on different characters"
Because 騎士団 is genuinely one nameplate shown x19, the user WILL see "Knights"
repeatedly — that matches what JP shows (騎士団). The only way a *distinct* NPC could
wrongly show "Knights" is the **glyph-page law**: the scan (and the live patcher) both
decode via the GLOBAL msg_glyph_map. If some scene's per-resource glyph page renders a
personal name whose ids collide with the global 騎士団 codepoints, the build would stamp
"Knights" on it. This CANNOT be settled statically — it needs a GS dump / screenshot of
the specific offending scene (R1207 has the most 騎士団 hits: check there first).

## FIX PLAN (prioritized)
1. **P0 – housekeeping:** the coverage gap is closed. Regenerate or delete the stale
   build/_nameislands_unmapped.json (Jun 27) + build/_untranslated_names_report.json
   (Jun 25); update MEMORY so audits stop re-chasing the phantom "13 missing / Adventurer
   x19." (Re-run build/_enum_nameislands.py — it already uses current data.)
2. **P1 – capture-gated verification:** if the user still reports a wrong "Knights" on a
   named character, capture that scene and test the glyph-page-collision hypothesis
   against the specific resource (per-resource decode, NOT the global map). Do not patch
   blind — anchor semantically in-resource (CLAUDE.md glyph-page law).
3. **P2 – taste call (optional):** 騎士団→"Knights" as a bare nameplate on many speakers
   may read oddly in English even though faithful. If lore shows individual knight
   speakers, consider "Knight"/"Guard" for those specific groups. This is editorial, not
   a coverage bug.

## Method / caveats
- Read-only. Reused build/_enum_nameislands.py decode logic in
  scratchpad/recon_names/_fresh_scan.py (writes nothing to project).
- Scanned R1190–R1360 (full nameplate family; full-corpus walk timed out but nameplates
  live here). Party-bar rosters (R1892 LE / R2654 sub-7) use the same name_labels.json
  and were already romanized in v161–v165.
- No fresh nameplate GS dump available (scratchpad/harpy recipe absent; ramdumps are old
  19/22/27-series saves predating the fix — would show stale data, not used).
