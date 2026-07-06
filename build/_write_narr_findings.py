# -*- coding: utf-8 -*-
content = """# recon2-N1-narr-root - FINDINGS

## Question
Why does the tavern-counter narration ("At Gin's tavern counter, requests were
offered to adventurers.") render CENTER-anchored / ragged instead of left-aligned
like the other proportional narrations?
(screenshot runs/.../shots/narration.png; live ramdumps/misalignednarration.p2s)

## TL;DR (CONFIRMED root cause)
Text = R1197, msg_index / group 2. It IS a NARRATION block in the engine (0x63
align op0 == 1), BUT its group also contains a 0x14 name-island label record, so
dialogue_classifier._classify deliberately DROPS it
(tools/dialogue_classifier.py:159-160 -- "nameplate in narration -> default").
That drop makes group 2 absent from BOTH build_dialogue_map(1197) and
build_narration_map(1197). In build/build_v9.py the per-group routing (lines
623-634) therefore falls through to the final "else: wrap_type2_text(...)" branch
(line 634), the legacy char-count wrapper, which NEVER calls
pad_narration_left_align (that call lives only in the "elif mi in
narration_groups:" branch, line 632). With no equal-count trailing-space padding,
the engine count-based per-line center-anchor draws each line centered on its own
width -> ragged center stack. Confirmed in live EE RAM: the five rendered lines
have glyph counts 15/8/13/10/12 with NO equalizing trailing-pad cells, whereas the
following group 3 ("As you / approached the / ...") DOES carry long trailing-pad
runs (correctly routed as narration and padded).

NOT a one-off: the same nameplate-in-narration skip drops 223 translated groups
corpus-wide (R1193, R1194, R1196, R1197, R1199-R1213, R1347-R1353). Group 2 is the
sampled one.

## Evidence chain

### 1. Which resource/group
data/type2_translated/batch_01.json:5564-5569
  resource 1197, msg_index 2,
  english: "At Gin's tavern / counter, / requests were / offered to // adventurers."
Authored with manual " / " line breaks + one " // " page break (5 pre-split lines).

### 2. Classifier drops group 2 (build never pads it)
Ran tools/dialogue_classifier.py on R1197:
- build_dialogue_map(1197)   -> group 2 NOT present
- build_narration_map(1197)  -> group 2 NOT present
- _classify(1197)[2]         -> None (absent from dict)
- neighbors: group 0 -> N, group 3 -> N, group 4 -> D
So in build/build_v9.py:
- line 623 "if mi in dialogue_groups:" -> False
- line 627 "elif mi in narration_groups:" -> False (this branch calls pad at line 632)
- line 633 "else: en_text = wrap_type2_text(en_text)" -> TAKEN, no padding.

### 3. WHY the classifier drops it - name-island inside a narration block
Section-1 walk of extracted/packdata_raw/1197_type02.raw:
- Group 2 byte range in Section 2 = (217, 266).
- Covering 0x04 DISPLAY block: pc=19246, off=221, cnt=74, end=295 -> covers groups [2,3].
  (coverage test "not (ge<off or gs>=end)" True for g2: ge=266>=off=221, gs=217<end=295)
- Nearest preceding mode-config 0x12 GOSUB = pc=19240, _helper_mode = 1 -> block mode N.
- 0x14 label records INTO group 2: off=217 (cnt=2) and off=219 (cnt=2) -> 2 in name_groups True.
- _classify skip (tools/dialogue_classifier.py:159-160):
    if gi in name_groups and mode == "N":
        continue   # nameplate in narration -> default
  -> group 2 skipped -> no entry returned.

The skip is by-design (handoff section 2 / project_box_mode_mechanism.md): in a
narration interlude the engine draws an inherited nameplate separately, and the
recon let such groups fall to the default char-wrap. But this group is real
centered narration body text, and the default path does NOT left-align it.

### 4. LIVE confirmation (ramdumps/misalignednarration.p2s, from v132 20:44)
Decompressed eeMemory.bin (Zstandard method-93 zip; 32 MB). Found the rendered
glyph stream by encoding (char-32)<<8 BE cells (gid in HIGH byte; break=0xFE00,
group-end=0xFF00). Parsed lines for this message:
  line 0: "At Gin's tavern"  glyphs ~15  trailing-pad ~0
  line 1: "counter,"         glyphs 8    trailing-pad 0
  line 2: "requests were"    glyphs 13   trailing-pad 1
  line 3: "offered to"       glyphs 10   trailing-pad 1
  line 4: "adventurers."     glyphs 12   trailing-pad 0
Different glyph counts, no equal-count pad -> engine center-anchors each line on its
own width -> ragged center stack (matches shots/narration.png).
The NEXT message in RAM (group 3, "As you / approached the / counter, the barkeep /
spoke") shows a long run of trailing 0x0000 pad cells -> it WAS padded (routed
through narration_groups). Direct A/B proof the pad pass works when reached and that
group 2 simply never reached it.

## Answer to the four sub-hypotheses
(a) "resource the pad pass never iterates" - NO. R1197 is iterated (g3 IS padded).
(b) "classified as something other than narration" - EFFECTIVELY YES, this is it.
    Engine-mode NARRATION, but classifier DROPS it from the narration map because it
    also has a 0x14 name-island, so build treats it as unclassified -> legacy
    char-wrap -> no pad.
(c) "authored without per-line groups" - NO. Proper " / " / " // " breaks;
    pad_narration_left_align would handle it if called.
(d) "different box mode" - NO. Same narration mode (op0>=1, align!=0, bw=313).

## Exact mechanism (file:line)
1. tools/dialogue_classifier.py:159-160 -- "if gi in name_groups and mode==N: continue"
   drops every narration group that also holds a 0x14 label island.
2. build/build_v9.py:627-634 -- pad_narration_left_align invoked ONLY inside
   "elif mi in narration_groups:" (627->632). A dropped group hits else (633-634)
   -> wrap_type2_text -> no padding.
3. Net: R1197 g2 (and 222 sibling groups) ship unpadded, count-based-centered.

## Scope / siblings (sweep over data/type2_translated/batch_*.json INTERSECT skip set)
TOTAL = 223 translated groups dropped by the nameplate-in-narration skip:
R1193[0], R1194[0]
R1196[4,202,533,694,702,704,709,715,727,810,811]
R1197[1,2,15,44,59,112,137,165,231,251,277,292,320,354,390,458,475,486,536,573,606,633,670,691,735,753,757,823,850,938]
R1199[102,129], R1200[1,64,65,118], R1201[128,133,152]
R1202[1,2,15,74,76,187,210,224,236,250,271,285]
R1203[1,2,24,28,63,386,503,517,538,572,576,628,642,648,717,726,753,762,774,787,801,847,867,1295,1297,1575,1617]
R1204[14,18,24,124,125,126,137,159,179,189,335,342,382,386,421,646,659,671,716,755,871]
R1205[16,67,71,330,356,378,382,417,642,746,758,764,787,806,829]
R1206[79,104,153,290,294,329,658,665,708,709,740,851,873]
R1207[179,232,233,320,324,359,585,646,790,810,869]
R1208[77,78,110,133,159,181,185,220,445,462,496,534,721]
R1209[7,8,26,54,192,196,231,553,569,581]
R1210[1,101,202,209,231,235,270,592]
R1211[1,54,76,80,115,356,395,519,588,589]
R1212[1,17,111,133,137,172,491,612,632]
R1213[1,4], R1347[2,6], R1348[1], R1349[4]
R1352[0,3,6,9,12,15,18]
R1353[1,17,111,133,137,172,485,606,626]

NOTE: not all 223 necessarily render as multi-line centered narration (some may be
single-line, or genuine nameplate prefixes where the skip is correct). The proven
misalignment is R1197 g2; the rest are the CANDIDATE sibling set sharing the same
code path.
CAVEAT: some entries are ALSO in SKIP_STRUCTURAL_GROUPS / DIALOGUE_WRAP_EXCLUDE
(build/build_v9.py:494, 511-512) -- e.g. R1197 g1 is structural-skip; R1212 g1 /
R1213 g1 / R1353 g1 are wrap-excludes (load-bearing list structure). A fix must
intersect-OUT those exclusion sets or it will re-introduce the request-menu softlock.

## Recommended fix direction (recon only; not implemented)
LEFT-ALIGN narration even when the group was dropped as nameplate-in-narration:
1. Build-side, narrowest: in build/build_v9.py capture the FULL classifier verdict
   (mode N INCLUDING name-island groups) and route those through wrap_px(...,
   NARRATION_BOX_PX, collapse=True) + pad_narration_left_align, EXCEPT any group in
   SKIP_STRUCTURAL_GROUPS / DIALOGUE_WRAP_EXCLUDE. The name-island label is a
   separate nameplate the engine draws itself; padding the body lines will not touch it.
2. Classifier-side: add build_narration_map_incl_nameplate() (or a flag) returning
   mode-N groups WITHOUT the line-159 skip; consume it for the pad/route decision
   while keeping the existing skip for nameplate handling. Keeps the 19/19 API intact.
Re-verify on a fresh narration save that R1197 g2 lines become equal glyph count
(padded to longest) with aligned left edges, and confirm no DIALOGUE group
(e.g. R1196 g577 Shady Man) regressed.

## needsLiveDebugger
- None required for the root cause (EE RAM glyph stream was conclusive).
- Recommended only to AUDIT the 222 sibling groups: confirm which actually render as
  multi-line centered narration vs single-line / legit nameplate cases, so the fix
  mode map is not over-broad. A static pre-filter (multi-line after wrap AND mode==N)
  helps; on-screen sampling of a few (R1202 g1, R1203 g1, R1352 g0) would validate.

## Files examined
- data/type2_translated/batch_01.json (5555-5575)
- build/build_v9.py (285-300, 490-512, 580-650)
- tools/dialogue_classifier.py (full)
- extracted/packdata_raw/1197_type02.raw (Section 1 walk; Section 2 group offsets)
- ramdumps/misalignednarration.p2s -> eeMemory.bin (glyph stream @ 0x11ce737)
- runs/.../shots/narration.png
"""
import os
p = os.path.join("runs","CLAUDE-RUNS","RUN-20260623-1835-box-request-formatting",
                 "subagents","recon2-N1-narr-root","FINDINGS.md")
with open(p, "w", encoding="utf-8") as f:
    f.write(content)
print("wrote", p, len(content), "bytes")
