# Busin 0: Wizardry Alternative Neo — English Fan Translation

An unofficial, community English translation of **Busin 0: Wizardry Alternative Neo**
(武神0 〜ウィザードリィ オルタナティブ ネオ〜), the PlayStation 2 dungeon-crawler RPG
released only in Japan. This repository holds the full translation toolchain: the
scripts that decode the game's text and graphics, the English translation data, and
the build pipeline that produces a patched, **real-PS2-compatible** disc image.

> **Status: Public Beta (v166 — "The Library Update").**
> Playable start to finish in English. Download the ready-made patch at
> **[busin0-en.pages.dev](https://busin0-en.pages.dev)** — you do not need this
> repository to play, only to build from source or contribute.

Target disc: **SLPM-65378** (original 2006 release — *not* the Atlus Best Collection
SLPM-65876). Every fix modifies the actual ISO data (game resources, EXE, font
atlases) so it runs on real hardware, not just emulators.

---

## For players — applying the patch

You need three things:

1. **Your own copy of the game**, dumped to an ISO. We distribute no game data.
   The patch expects the original Japanese disc:
   - Filename doesn't matter, contents do.
   - **Source ISO MD5:** `48a5639afdf9931913c7dde298dc5349`
   - If your dump's MD5 differs, you have a different revision and the patch will
     not apply cleanly.
2. **The patch file:** `busin0_en_v166.xdelta` (~1.0 MB), from
   [busin0-en.pages.dev](https://busin0-en.pages.dev).
3. **An xdelta3 tool** — either the command line or a GUI.

### Command line

```bash
xdelta3 -d -s "Busin 0 (Japan).iso" busin0_en_v166.xdelta BUSIN0_EN.iso
```

### GUI (Delta Patcher, Windows)

1. Open Delta Patcher.
2. **Original file** = your Japanese ISO.
3. **XDelta patch** = `busin0_en_v166.xdelta`.
4. Click **Apply Patch**. It writes the English ISO next to the original.

### Verify the result

Check the MD5 of the output ISO:

- **Patched ISO MD5:** `76a75374b0e6f2e7b8e767a1d545b408`

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

Bug reports are welcome. Please include: the **patch version** (v166 beta), where in
the game it happens (screen/menu/scene), what you expected vs. what you saw, and a
screenshot if you can. Discussion happens in the r/wizardry community thread linked
from the site.

---

## What's translated

As of v166 the translation is **effectively complete** — you can play the whole game
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

### Release history

| Version | Theme |
|--------:|-------|
| v151 | First public beta — dialogue, menus, most UI. |
| v160 | Spell descriptions & names, battle prompts, pill-popup fix, letter spacing. |
| v162 | Ending narration, ~440 missing town lines, nameplates, class/trait audit. |
| v166 | **The Library Update** — entire in-game library (text + banner art), ~900 repaired/new dialogue lines, game-wide name unification. |

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
resource edits, a **300-test regression suite** (`tests/`), and an **MD5 round-trip
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
python tools/generate_font_atlas.py && python build/build_v9.py && cp build/BUSIN0_EN_v9.iso build/BUSIN0_EN_v166.iso
```

Always rebuild and copy in one command — the build writes the archive directory size
as its final step, and copying mid-build produces a truncated ISO.

**Verify and test**

```bash
python verify_iso.py build/BUSIN0_EN_v166.iso   # structural checks on the built ISO
python tests/run_all.py                         # the full regression suite (300 tests)
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

## Credits & disclaimer

This is an **unofficial fan project**, not affiliated with or endorsed by Atlus,
RACJIN, or any rights holder. *Busin 0: Wizardry Alternative Neo* and *Wizardry* are
trademarks of their respective owners. **No copyrighted game data is distributed in
this repository** — you must supply your own legally-obtained disc image.

English naming follows the official Western *Wizardry: Tale of the Forsaken Land*
(Busin 1 / SLUS-20259) localization where the two games share monsters, spells, and
terms, with the community fan guide as a secondary reference.

Built by the Busin 0 translation community. Contributions and bug reports welcome.
