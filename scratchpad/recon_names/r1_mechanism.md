# RECON 1 — NPC Nameplate Mechanism + "Knights"/Plural Audit

## Nameplate compositor pipeline (which source feeds what)

There are THREE distinct name renderers. They do NOT share a path:

1. **NPC dialogue SPEAKER nameplate** (the "Knights" the user is hitting)
   - Source: a **0x14 NAME/LABEL opcode** whose glyph slice is a **clean PREFIX of a
     Section-2 group** in a **type-02 dialogue resource**.
   - Build owner: **tools/patch_section1_offsets.py** (build_v9 **Step 4**,
     `inject_and_patch`). For each translated group whose 0x14 slices are a clean
     prefix, it rebuilds them as `[English label][English body]`.
   - Label text = decode the JP glyph slice via **data/msg_glyph_map.json**, then look
     up **data/name_labels.json**. Hit → English label. Miss → JP glyphs kept verbatim.
   - **TO FIX A NAMEPLATE: edit `data/name_labels.json`** (the value for the JP key).
   - NOTE: only clean-PREFIX slices are romanized; **mid-group** knight labels are left
     as raw JP glyphs (render Japanese, not English).

2. **Party-bar roster names** (bottom-of-town bar; party MEMBERS, not NPC speakers)
   - REAL source: **R1892** (`1892_type20.raw`, little-endian) via
     **tools/patch_r1892_names.py**. R2654 sub-7 via **tools/patch_r2654_names.py** is
     off the bar's path (big-endian; kept in sync anyway).
   - Both GATED by `data/r2654_party_names.json` allowed set (only ~30 party-member
     names: Vera, Konde, Erika, ...). Knight nameplates are NOT in this set → these
     patchers never touch them.

3. **Library names** (monster/spell/AA in the in-game library): tools/patch_r2654_library.py.

Order (MEMORY note) `patch_r2654_names → patch_r2654_library → patch_r1892_names` is the
R2654/R1892 roster chain — **irrelevant to NPC dialogue nameplates**.

## Root cause of the plural "Knights" (glyph-page law)

The SAME on-screen knight-speaker nameplate is encoded with **two different glyph
pages** in different resources, and the two decodes were romanized INCONSISTENTLY:

| page | glyph ids | msg_glyph_map decode | name_labels value |
|------|-----------|----------------------|-------------------|
| A    | [297,280,286] | 士騎戦 | **"Knight"** (line 70 — the earlier fix) |
| B    | [483,494,510] | 騎士団 | **"Knights"** (line 72 — STILL PLURAL) |

Page B was independently proven by the badge fix (騎=483,士=494,団=510,長=404; R1198
nameplate). So page-B [483,494,510] genuinely renders 騎士団 on screen; as a *speaker*
nameplate for an individual knight it should read **"Knight"** to match its page-A twin,
not the collective "Knights". This is the systemic inconsistency the user is hitting.

Related: R1198 nameplate is [483,494,510,**404**] = 騎士団長 cnt=4 → "Commander" (correct;
if a slice ever captured only 3 of the 4 glyphs it would collapse to "Knights").

## Every current plural/collective NPC nameplate (0x14 PREFIX label islands)

Static scan of all type-02 resources (excluded R680–911 binary-noise + >400KB blobs).
"PREFIX" = actually rendered as a speaker nameplate. Fix target = the JP key in
`data/name_labels.json`.

| Resource / offset | slice | JP decode | current EN | assessment / likely-correct |
|---|---|---|---|---|
| R1196 off=7442  | [483,494,510] | 騎士団 | **Knights** | speaker nameplate → **"Knight"** |
| R1197 off=31825 | [483,494,510] | 騎士団 | **Knights** | speaker nameplate → **"Knight"** |
| R1203 off=18166 | [483,494,510] | 騎士団 | **Knights** | speaker nameplate → **"Knight"** |
| R1207 off=4444  | [483,494,510] | 騎士団 | **Knights** | speaker nameplate → **"Knight"** |
| R1355 off=90    | [483,494,510] | 騎士団 | **Knights** | speaker nameplate → **"Knight"** |
| R1210 off=21253 | [253,231,200,233,483,494,510] | ドラクル騎士団 | **Dracul Knights** | order name; if single speaker → "Dracul Knight" (taste call) |
| R1198 off=675   | [483,494,510,404] | 騎士団長 | Commander | CORRECT (leave) |

All 5 plain-"Knights" plates share **ONE json key**: `data/name_labels.json` line 72
`"騎士団": "Knights"`. Changing that single value to `"Knight"` fixes all five at once
(the value is applied only to 0x14 nameplate islands, never to body text — body 騎士団
"the Knights/Order" comes from the type-2 batch translations and is untouched).

### Already-correct / not-plural (for completeness)
- Page-A "Knight" nameplates (unchanged, correct): R1196 off=24369, R1203 off=32062,
  R1204 off=1629, R1205 off=1468, R1207 off=25748 (all [297,280,286] 士騎戦 → "Knight").
- Mid-group (NOT romanized by build → render JP, separate issue): R1194 off=339
  士騎戦動, R1206 off=7337 士騎戦, R1197 off=28585 女騎士 (Lady Knight), R1202 off=2727/2771/2778
  騎士/個騎士/扱騎士 (class-name list: Knight/Paladin/Dark Knight).
- R1204 off=2883 [483,494,233,272,210] 騎士ルッツ → "Knight Lutz" (PREFIX, singular, fine).

## name_labels.json — all Knight-family keys (current)
```
70  "士騎戦": "Knight"          (page-A speaker plate; the earlier fix)
71  "女騎士": "Lady Knight"
72  "騎士団": "Knights"   <-- SYSTEMIC PLURAL, feeds all 5 page-B plates above
73  "騎士団長": "Commander"
74  "ドラクル騎士団": "Dracul Knights"
75  "騎士ルッツ": "Knight Lutz"
143 "騎士": "Knight"            (class list)
144 "きし": "Knight"
155 "個騎士": "Paladin"
157 "扱騎士": "Dark Knight"
158 "くろきし": "Dark Knight"
```

## Save-state evidence
`ramdumps/` has the relevant captures (newest first):
- **anotherknights.p2s** — 2026-07-06 19:41 (TODAY; the "second one" the user just hit)
- **knightsguy.p2s** — 2026-07-05 21:50
- ladyknightnoportrait.p2s (2026-06-13), knighterguy/knightguy.ps2 (2026-05-23, STALE)

Not RAM-decoded in this recon (static evidence is conclusive), but they correspond to
the R1196/R1197/R1203/R1207 hub-family "Knights" plates above.

## Recommended fix (do NOT apply here)
Edit **data/name_labels.json** line 72 `"騎士団": "Knights"` → `"Knight"`.
Consider R1210 `"ドラクル騎士団": "Dracul Knights"` → `"Dracul Knight"` only if the speaker is
a single knight (verify in-scene). R1196/1203/1207 are the **softlock-history
R1196–R1213 family** — the name_labels comment mandates a **fresh-boot menu test** after
any change. Rebuild via normal Step-4 pipeline; nameplate change is size-neutral for a
3-glyph JP slice → "Knight" (5 chars fits).
