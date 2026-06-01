# PCSX2 ISO Path Investigation

## Key Findings

### 1. GameList Configuration
PCSX2 config at: `C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\inis\PCSX2.ini`

The `[GameList]` section has:
```
Paths = C:\Programmieren\wizardrytranslation
```

This is the **project root**, NOT the `build/` subdirectory. PCSX2 scans this
directory (non-recursively by default) and shows found ISOs in the game list.

### 2. ISOs Found at Project Root (what PCSX2 sees first)
- `Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso` -- 1,274,544,128 bytes (ORIGINAL JP)
- `Wizardry - Tale of the Forsaken Land (USA).iso` -- 580,290,560 bytes
- `Wizardry - Tale of the Forsaken Land (USA).bin` -- 666,427,440 bytes
- `ee_memory_fight1.bin` -- 33,554,432 bytes (memory dump, not a game)

### 3. Gamelist Cache Contents
The binary cache at `cache/gamelist.cache` contains exactly 3 entries:
1. `C:\Programmieren\wizardrytranslation\Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso` (SLPM-65378)
2. `C:\Programmieren\wizardrytranslation\Wizardry - Tale of the Forsaken Land (USA).bin` (SLUS-20259)
3. `C:\Programmieren\wizardrytranslation\Wizardry - Tale of the Forsaken Land (USA).iso` (SLUS-20259)

**NONE of the build ISOs (BUSIN0_EN_v29.iso etc.) appear in the cache.**

### 4. Build ISOs (28 versions!)
All in `C:\Programmieren\wizardrytranslation\build\`:
- `BUSIN0_EN.iso` (no version)
- `BUSIN0_EN_v3.iso` through `BUSIN0_EN_v29.iso`
- All are 1,274,544,128 bytes (same size as original)

### 5. Risk Assessment

**LOW RISK of loading the wrong file** -- because:
- The user likely launches the game by right-clicking or double-clicking a
  specific ISO in the PCSX2 game list, or by dragging the ISO onto PCSX2
- PCSX2 does NOT scan `build/` (it only scans the root, non-recursively by default)
- The build ISOs do not appear in the gamelist cache at all

**However**, if the user is launching from the PCSX2 game list UI (not dragging
or selecting a file manually), they would be launching the **original untranslated
JP ISO** (`Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso`), NOT any
translated build.

### 6. Recommendation
- Ask the user: "How do you launch the game? From the PCSX2 game list, or by
  opening a specific ISO file?"
- If from the game list: they are likely playing the ORIGINAL, not v29
- Consider adding `build/` to the PCSX2 game list paths, or changing the path
  from the project root to `build/` specifically
- Alternatively, copy/replace the root ISO with the latest build
