# Busin 0: Wizardry Alternative Neo — English Fan Translation

An unofficial, community English translation of **Busin 0: Wizardry Alternative Neo**
(武神0 〜ウィザードリィ オルタナティブ ネオ〜), the PlayStation 2 dungeon-crawler RPG
released only in Japan. This repository holds the full translation toolchain: the
scripts that decode the game's text and graphics, the English translation data, and
the build pipeline that produces a patched, **real-PS2-compatible** disc image.

> **Status: Public Beta (v182).**
> Playable start to finish in English. Download the ready-made patch at
> **[busin0-en.pages.dev](https://busin0-en.pages.dev)** — you do not need this
> repository to play, only to build from source or contribute.

Target disc: **SLPM-65378** — the original release, software **version 1.03**. This is
*not* the Atlus Best Collection (SLPM-65876), which is version 2.01 and is a separate,
later "bug-fix" pressing. (Some dumps of SLPM-65378 are mislabeled "v2.01" in their
filename; ignore the filename and trust the MD5 below.) Every fix modifies the actual
ISO data (game resources, EXE, font atlases) so it runs on real hardware, not just
emulators.

---

## For players — applying the patch

You need three things:

1. **Your own copy of the game**, dumped to an ISO. We distribute no game data.
   The patch expects the original Japanese disc:
   - Filename doesn't matter, contents do.
   - **Source ISO MD5:** `48a5639afdf9931913c7dde298dc5349`
   - If your dump's MD5 differs, you have a different revision and the patch will
     not apply cleanly.
2. **The patch file:** `busin0_en_v182.xdelta` (~1.0 MB), from
   [busin0-en.pages.dev](https://busin0-en.pages.dev).
3. **An xdelta3 tool** — either the command line or a GUI.

### Command line

```bash
xdelta3 -d -s "Busin 0 (Japan).iso" busin0_en_v182.xdelta BUSIN0_EN.iso
```

### GUI (Delta Patcher, Windows)

1. Open Delta Patcher.
2. **Original file** = your Japanese ISO.
3. **XDelta patch** = `busin0_en_v182.xdelta`.
4. Click **Apply Patch**. It writes the English ISO next to the original.

### Verify the result

Check the MD5 of the output ISO:

- **Patched ISO MD5:** `cdf272695faf4c8551c65055db7e34eb`

If it matches, the patch applied perfectly. Boot `BUSIN0_EN.iso` in your PS2, or in
PCSX2 via **File → Boot ISO**.

> ⚠️ **PCSX2 testers:** always boot fresh from the title screen. Save states
> (`.p2s`) embed the full 32 MB of console RAM including all loaded game text, so a
> save state made on an older build will show old text no matter which ISO is
> mounted. Don't trust save states for judging a new patch.

> ℹ️ **The game deletes your memory-card save on every load — this is intentional**
> (a roguelike anti-save-scum mechanic), not a patch bug. Back up your memory card
> if you want to preserve a run.

### Found a problem?

Bug reports are welcome. Please include: the **patch version** (v182 beta), where in
the game it happens (screen/menu/scene), what you expected vs. what you saw, and a
screenshot if you can. **[GitHub Issues](https://github.com/Fabulu/Busin0Translation/issues)**
is the best place to report (you can attach save states and screenshots directly); the
r/wizardry community thread works too.

---

## What's translated

As of v182 the translation is **effectively complete** — you can play the whole game
in English:

- All story **dialogue and narration**, including the intro and ending narration.
- The **entire in-game Library** (100%): monster compendium with official English
  bestiary names, magic library, the Adventurer's Guide, glossary, key items, book
  texts, journals — and even the decorative banner artwork.
- **Battle** techniques, spells, item and status text, and all battle-menu prompts.
- **Character creation**, class/trait names, and all facility & town-hub menus.
- **Pre-rendered UI graphics** (buttons, tabs, status labels) re-drawn in English.
- Ally roster names, NPC nameplates, and all player-visible EXE strings.

### Known remaining items (small)

- **Credits / staff roll** — likely a burnt-in video stream; capture-gated.
- **Equipment type icons** (weapon-category glyphs) — capture-gated, not yet
  confirmed on screen.
- **Ending render verification** — the ending text is translated but no end-game
  screenshot has confirmed the on-screen result yet.
- **Item-name capsule** — widened in v180 so long English names fit; the new width
  hasn't been eyeballed in-game yet. Reports welcome.
- **Two micro-spacing overlaps** (the in-battle equipped-marker "EHealing" and the
  alchemy-shop name/quantity collision) — analyzed, wait on a live-debugger session.

### Release history

| Version | Theme |
|--------:|-------|
| v151 | First public beta — dialogue, menus, most UI. |
| v160 | Spell descriptions & names, battle prompts, pill-popup fix, letter spacing. |
| v162 | Ending narration, ~440 missing town lines, nameplates, class/trait audit. |
| v166 | **The Library Update** — entire in-game library (text + banner art), ~900 repaired/new dialogue lines, game-wide name unification. |
| v167 | Polish — Bishop class description fix, flagged dialogue/item-name cleanups, unified spellings. |
| v168 | Character-creation trait wording (Bold, Superstitious, Narcissist). |
| v171–v173 | Choices that showed only a continue-arrow fixed, scattered/wrong on-screen text fixed, dungeon signs & shops repaired, name/label corrections — plus two *incomplete* attempts at the battle softlock (each later shown insufficient). |
| v174 | **Pulled** — an EXE-extension experiment the console's loader rejected; it booted to the BIOS. |
| v180 | **The real battle fix** (boot-confirmed, harpy included): translation font data relocated out of battle memory for good. Character creation restored to full polish (letter spacing, gender symbols, description banner) and the item-name capsule widened. |
| v181 | Consistency polish — duplicate personality trait resolved, library trait pages aligned with character creation, name spellings unified. Game code identical to v180. Plus a wave of new build safeguards from a full-repo audit. |
| v182 | **The Language Update** — the deepest text pass yet: ~1,500 story lines that shipped as terse fragments rewritten as full dialogue (from the classic fan guide, cross-checked line by line), wrong quest objectives corrected, item categories (rings/talismans/stones) and famous-sword names sorted out, and personality traits both corrected and shortened to fit the recruitment screen. Beta-report fixes (tavern intro, trap game, inn greeting). Game code byte-identical to v180/v181. |

---

## How it works

The game keeps almost everything in one big resource archive, `PACKDATA.DIG`, plus
the main executable `SLPM_653.78`. Translating it means editing those in place and
rebuilding a valid ISO.

- **Resource container.** `PACKDATA.DIG` holds ~2,880 numbered resources (dialogue
  scripts, fonts, pre-rendered UI strips, item databases). Each has a type; the two
  big ones are *type-01* flat text and *type-02* scripted text with a bytecode
  section.
- **Text encoding.** In-game text is a stream of 16-bit **glyph indices**, split into
  groups by `FFFF` markers. Critically, **glyph IDs are per-resource page slots** —
  the same numeric ID renders a *different* character in a different resource, so a
  single global glyph map is only an approximation. All decoding is anchored
  semantically inside each resource, never by borrowing another resource's mapping.
  (This "glyph-page law" is the root cause of several bugs fixed over the project.)
- **Script bytecode.** type-02 resources carry a byte-addressed big-endian opcode
  stream that references the text. When translated English changes a string's length,
  the offsets in that bytecode are re-derived by a BFS disassembler
  (`tools/sec1_disasm.py`) — never by fragile pattern matching.
- **Fonts & layout.** English needs proportional metrics the Japanese engine didn't
  ship, so the EXE is patched with new glyph-width tables and small code "caves" that
  relocate cleanly into safe memory regions.
- **The build.** English text lives as JSON in `data/`. Injectors rewrite each
  resource, the EXE is patched, `PACKDATA.DIG` is rebuilt, and a fresh ISO is
  assembled — including an automatic relocation step so the (larger) rebuilt archive
  doesn't overrun the next file on the disc.

### Safety philosophy

Because a single stray byte can corrupt a font or crash the VIF/GS upload, the build
leans hard on gates: **pristine-diff checks** (every byte outside an intended edit
window must be byte-identical to the original), **containment asserts** on pixel and
resource edits, a **345-test regression suite** (`tests/`), and an **MD5 round-trip
gate** on every release patch. Failed build steps abort loudly rather than shipping
stale output.

---

## Building from source

You need the game data yourself — this repo contains **no copyrighted game content**.

**Prerequisites**

- Python 3.x with **Pillow** (font atlas rendering) and **pyxdelta** (patch encode).
- Your own legally-dumped Japanese ISO, placed at the repo root as
  `Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso`.
- The extracted resource assets under `extracted/` (produced by the extraction
  scripts from your disc; not distributed here).

**Build the English ISO**

```bash
python tools/generate_font_atlas.py && python build/build_v9.py && cp build/BUSIN0_EN_v9.iso build/BUSIN0_EN_v182.iso
```

Always rebuild and copy in one command — the build writes the archive directory size
as its final step, and copying mid-build produces a truncated ISO.

**Verify and test**

```bash
python verify_iso.py build/BUSIN0_EN_v182.iso   # structural checks on the built ISO
python tests/run_all.py                         # the full regression suite (345 tests)
```

The finished disc image lands in `build/`.

---

## Repository map

| Path | Contents |
|------|----------|
| `build/` | The build pipeline (`build_v9.py` and its stages), injectors, EXE patcher. |
| `tools/` | Reusable tooling: font atlas, script disassembler/patcher, per-resource patchers. |
| `data/` | The English translation data (JSON) plus glyph maps and reference tables. |
| `tests/` | The regression suite guarding every shipped fix. |
| `extracted/` | Pristine resources extracted from your own disc (git-ignored / not distributed). |
| `release/` | Encoded `.xdelta` patches. |
| `runs/` | Recon and audit history from the reverse-engineering work. |
| `docs/` | Format notes and deeper design write-ups. |

`CLAUDE.md` is the load-bearing engineering doc — the build pipeline, resource
formats, and hard-won rules ("R1188 ships pristine", the glyph-page law, the overflow
self-heal) are documented there.

---

## The toolchain (for programmers)

`tools/` and `build/` hold **two kinds of scripts**. The load-bearing ones below make
up the reproducible build and are wired into `build/build_v9.py`. Everything else —
the large `analyze_*`, `find_*`, `scan_*`, `dis*`, `parse_gs_*`, `deswizzle_*`,
`search_*` families — is **reverse-engineering history**: one-off probes, disassembly
experiments, and GS-dump forensics kept for the record but not part of any build. If a
script isn't listed here or called by `build_v9.py`, treat it as archaeology.

### Build orchestration

| Script | Role |
|--------|------|
| `build/build_v9.py` | **The master build.** Runs every stage below in order, gates each on exit code, rebuilds `PACKDATA.DIG`, and assembles + relocates the ISO. Start here. |
| `build/build_full_english_v2.py` | Stage 1: the v2 text pipeline — injects all type-01 flat-text resources (dialogue, R34/R39 bases). |
| `tools/generate_font_atlas.py` | Renders the English glyph atlas; must run **before** `build_v9.py`. |
| `build/rebuild_packdata.py` | Repacks the patched resources back into `PACKDATA.DIG` with a correct directory. |
| `build/patch_exe.py` | Applies every EXE patch — font-width/metric tables, relocated code caves, SJIS strings — to `SLPM_653.78`. |

### Core reusable libraries

| Script | Role |
|--------|------|
| `tools/sec1_disasm.py` | BFS disassembler for type-02 **Section-1 bytecode**; recovers text references so offsets can be re-derived when English changes length. The heart of safe script patching. |
| `tools/patch_section1_offsets.py` | Uses the disassembler to rewrite Section-1 offsets after a type-02 text change. (Pattern matching is banned here — see `CLAUDE.md`.) |
| `tools/glyph_metrics.py` | Single source of truth for the proportional font-width tables the EXE patches install. |
| `tools/dialogue_classifier.py` | Decides dialogue vs. narration per text group (drives box layout / pagination). |
| `tools/encode_english_text.py`, `tools/encode_all_translations.py` | Encode English strings into the game's per-resource glyph-index streams. |
| `tools/extract_packdata_raw.py` | Extracts the pristine resources from your disc into `extracted/` (the build's diff baseline). |

### Resource injectors & patchers (called in order by `build_v9.py`)

| Script | Target |
|--------|--------|
| `build/inject_r39_v2.py`, `inject_r39_quest.py` | R39 — equipment, quest UI/titles. |
| `tools/patch_r39_inline.py`, `patch_r39_spell_desc.py`, `patch_r39_aa.py` | R39 — spell names, spell descriptions, battle-technique (AA) content. |
| `build/inject_r46_r47.py` | R46/R47 — bulletin board (with the v160 trailing-`FFFE` pill fix). |
| `tools/patch_r2100.py` | R2100 — the chargen upright 16px font atlas. |
| `tools/patch_r2138.py` | R2138 — the stat-label / class-header atlas (in-place pixel re-ink). |
| `tools/patch_r1193_narration.py`, `patch_r1194_narration.py` | Intro and ending narration line records. |
| `build/inject_r34_db.py` | R34 — item database. |
| `tools/patch_r2654_names.py`, `patch_r2654_library.py`, `patch_r1892_names.py` | R2654/R1892 — roster names and the variable-length **library** name subs. |
| `tools/patch_r2655_library_strips.py` | R2655 — the library banner / tab / footer artwork, re-inked to English. |
| `tools/patch_pill_widen.py` | R2139/R2138 — widens the item-name capsule (geometry record + box-art re-ink, v180). |
| `tools/patch_r2124.py`, `patch_r1365.py`, `patch_battle_strips.py`, `patch_camp_strips.py`, `patch_facility_strips.py`, `patch_r2147.py`, `patch_r1370.py`, `patch_r2880.py`, `patch_r2881_ending.py`, `patch_r2882_grave.py` | Pre-rendered UI strips — town hub, facilities, battle/camp chrome, status, intro/ending/grave cutscenes. |

### Verification

| Script | Role |
|--------|------|
| `verify_iso.py` | Structural check of a built ISO (TOC, resource integrity, relocation). |
| `tests/run_all.py` | The full regression suite (345 gates) — pristine-diff, containment, and structural invariants. |
| `build/rebuild_packdata.py`, `verify_iso.py` | Together enforce the overflow self-heal + relocation MD5 gate at ISO-build time. |

Patch releases are encoded with `pyxdelta` and round-trip-verified (apply to the JP
source, confirm the output MD5) before publishing.

---

## Credits & disclaimer

This is an **unofficial fan project**, not affiliated with or endorsed by Atlus,
RACJIN, or any rights holder. *Busin 0: Wizardry Alternative Neo* and *Wizardry* are
trademarks of their respective owners. **No copyrighted game data is distributed in
this repository** — you must supply your own legally-obtained disc image.

English naming follows the official Western *Wizardry: Tale of the Forsaken Land*
(Busin 1 / SLUS-20259) localization where the two games share monsters, spells, and
terms, with the community fan guide as a secondary reference.

Built by the Busin 0 translation community. Contributions and bug reports welcome.
