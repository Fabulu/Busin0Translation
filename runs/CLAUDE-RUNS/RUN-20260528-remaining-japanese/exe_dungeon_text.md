# EXE Dungeon & Exploration Text Analysis

**Date:** 2026-05-28  
**EXE:** `extracted/SLPM_653.78` (4,185,776 bytes)  
**ELF layout:** Single LOAD segment, file offset 0x80 -> VA 0x100000, size 0x3FDC80

---

## Executive Summary

**No player-visible dungeon/exploration text is hardcoded in the EXE.**

All dungeon text that players see (floor names, location descriptions, compass directions,
trap prompts, door/switch interactions) comes from:
- **MSG resources** (R48 for location names, R49 for dungeon interaction messages)
- **Cockpit HUD texture** (compass directions N/S/E/W, floor indicator)
- **Runtime glyph rendering** via the MSG system

The EXE contains only:
1. Internal room/event ID tables (ASCII, not displayed)
2. 3D model asset name tables (ASCII, not displayed)
3. Debug/TTY printf strings (not player-visible)

---

## Findings by Category

### 1. Floor Labels (B1F, B2F, ... B11F)

**No player-visible floor labels in the EXE.**

The EXE contains an internal **Room ID Table** at `0x3FAB70`-`0x3FB4A0` with 148 entries.
These are 16-byte null-padded ASCII strings used as resource/encounter lookup keys:

| Range | Entries | Example |
|-------|---------|---------|
| `0x3FAB70`-`0x3FAC40` | 12 | `B01F_0_01` through `B01F_4_03` |
| `0x3FAC50`-`0x3FAD70` | 19 | `B02F_0_01` through `B02F_4_03` |
| ... | ... | ... |
| `0x3FB3F0`-`0x3FB4A0` | 10 | `B11F_0_01` through `B11F_4_09` |

Format: `BxxF_Y_ZZ` where xx=floor (01-11), Y=area variant (0-4), ZZ=room number.

These are **internal lookup keys** for loading dungeon room data (geometry, encounters,
events). They are never displayed to the player. The player-visible floor indicator
(e.g., "B1F") is rendered by the cockpit HUD system, likely from texture data or
runtime glyph rendering.

The only format string referencing floor numbers is a **debug-only** printf:
- `0x3E9DFE`: `"Treasure Get Data MAX Over!!!(Floor=%dF:ID=%d)\n"` (TTY debug)

**Action needed: NONE** -- these are internal IDs, not display text.

### 2. Compass Directions (N/S/E/W)

**No compass direction text in the EXE.**

Search results:
- SJIS 北(N): 0 hits anywhere in EXE
- SJIS 南(S): 2 hits in code section (MIPS instruction coincidence)
- SJIS 東(E): 31 hits in code section (MIPS instruction coincidence)
- SJIS 西(W): 16 hits total, 6 in data section -- all false positives (pointer values 0x90BC appearing in struct data)
- ASCII "North"/"South"/"East"/"West": 0 hits
- Glyph-encoded 北/南/東/西: NOT IN GLYPH MAP (IDs don't exist)

**Conclusion:** Compass directions are rendered from the **cockpit HUD texture**, not from
EXE-hardcoded text. The compass is part of the dungeon exploration UI overlay, which is a
graphical element.

**Action needed: NONE in EXE** -- compass is a texture/graphical element, not EXE text.

### 3. Map Feature Labels

**No map feature labels in the EXE.**

The automap system (`Map Init!!!` debug string at `0x3EA210`) renders the dungeon map
procedurally. No text labels for map features (walls, doors, stairs, etc.) were found.

### 4. Trap Names

The EXE contains **debug-only** trap type names in ASCII printf strings. These are
developer TTY output, never shown to players:

| Offset | Debug String | Trap Type |
|--------|-------------|-----------|
| `0x3DF2E0` | `"Bar Trap Start(%d)!!!\n"` | Bar/gate trap |
| `0x3EA000` | `"Trap PoisonGas Start!!!\n"` | Poison gas |
| `0x3EA040` | `"Trap StoneGas Start!!!\n"` | Petrification gas |
| `0x3EA080` | `"Trap DarkFog Start!!!\n"` | Darkness fog |
| `0x3EB660` | `"Trap Spear Start!!!\n"` | Spear trap |
| `0x3EB6E0` | `"Trap RoofFall Start!!!\n"` | Ceiling collapse |
| `0x3EB740` | `"Trap CrossBow Start!!!\n"` | Crossbow trap |
| `0x3EB7A0` | `"Trap MPDrain Start!!!\n"` | MP drain trap |
| `0x3EB7E0` | `"Trap Alarm Start!!!\n"` | Alarm trap |
| `0x3EB820` | `"Trap Teleporter Start!!!\n"` | Teleporter trap |
| `0x3E9C70` | `"TrapSiphon Init!!!\n"` | Siphon/drain |

These reveal the game's internal trap type enumeration. The player-visible trap names
(shown when a trap is triggered) come from **R49 MSG resources**.

**Action needed: NONE** -- all TTY debug strings.

### 5. Door/Switch Prompts

No player-visible door or switch prompts in the EXE. The debug strings confirm:
- `0x3E9730`: `"Dun Door Set(%d)!!!\n"` (TTY)
- `0x3E9770`: `"Dun Way Set(%d)!!!\n"` (TTY)
- `0x3EB8A0`: `"Wall Break Work Cut!!!\n"` (TTY)

Door/switch interaction prompts come from **R49 MSG resources**.

### 6. Event System

The EXE contains an **Event ID Table** at `0x3FB4B0`-`0x3FB9F0` with 85 entries:

| Prefix | Count | Range |
|--------|-------|-------|
| EV01-EV12 | 80 | Main dungeon events (floors 1-12) |
| ED1-ED3 | 5 | End/special events |

Format: `EVxx_YY` where xx=event group, YY=event number.
These are internal event script lookup keys, not displayed text.

Related debug strings:
- `0x3F3960`: `"***  Event Start   ***\n"`
- `0x3F3920`: `"***  Event End   ***\n"`
- `0x3F3770`: `"!!!!!   Event Bgm Chage   !!!!!\n"`

**Action needed: NONE** -- internal IDs and debug output.

---

## 3D Model Asset Name Table

Located at `0x3E6B80`-`0x3E8D30`, contains 356 unique ASCII model names for dungeon
geometry. Structure per floor (10 floors + special):

| Model Type | Pattern | Example | Purpose |
|------------|---------|---------|---------|
| Door models | `bXXa_door_a/b` | `b01a_door_a` | Door meshes (2 variants per floor) |
| Wall segments | `bXXa_wall` | `b01a_wall` | Wall geometry |
| Floor tiles | `bXXa_yuka` | `b01a_yuka` | Floor geometry (yuka = floor) |
| Stairs up | `bXXa_up` | `b01a_up` | Upward staircase |
| Stairs down | `bXXa_down` | `b01a_down` | Downward staircase |
| Corridor | `bXXa_NN_a/b` | `b01a_03_a` | Corridor/passage segments |
| Curves | `bXXa_curve_a/b` | `b01a_curve_a` | Curved corridor segments |
| Special (sp) | `bXXa_spNN` | `b01a_sp02` | Special room features |
| Death door | `death_door` | -- | Death/boss door |
| Destructible | `bXXa_koware_a/b` | `b01a_koware_a` | Breakable walls (koware = broken) |
| Death room | `bXXa_death_a/b` | `b01a_death_a` | Death trap rooms |

**Action needed: NONE** -- internal 3D asset references, never displayed.

---

## Preceding Data Tables (Context)

The room/event table is preceded by other internal asset tables:

| Offset Range | Prefix | Purpose |
|--------------|--------|---------|
| `0x3FA900`-`0x3FA960` | `ARD_SM_xx` | Sound/music asset IDs |
| `0x3FA990`-`0x3FAA10` | `DJC_xx` | DJ/jukebox control IDs |
| `0x3FAA20`-`0x3FAA70` | `DSM_xx` | Sound module IDs |
| `0x3FAA80`-`0x3FAAB0` | `DJF_xx` | DJ file references |
| `0x3FAAC0`-`0x3FAB40` | `DT_xx` | Data table references |
| `0x3FAB50`-`0x3FAB60` | `DTE_xx` | Data table event references |

All are internal asset lookup keys.

---

## Debug String Inventory (Dungeon System)

All dungeon-related debug strings (TTY output, never player-visible):

| Offset | String | System |
|--------|--------|--------|
| `0x3E0040` | `"Floor %d, (ex:%f,dun:%f,lv%f)\n"` | Floor loading |
| `0x3E9500` | `"Set FloorRate %d(%f)\n"` | Difficulty scaling |
| `0x3E9520` | `"Dungeon Data Access Error...GetDungeonDataPos.\n"` | Error handler |
| `0x3E9560` | `"Dungeon Data Access Error...GetDungeonDataTextEventNo.\n"` | Error handler |
| `0x3E9630` | `"Dungeon Wall & Door Init Err!!!\n"` | Init error |
| `0x3E9660` | `"Free Room Tbl Num(%d:%d)/(%x)!!!\n"` | Room table debug |
| `0x3E96B0` | `"Dungeon Copy GetMax Over!?(%d)\n"` | Overflow check |
| `0x3E96D0` | `"roomnum%d = %x (Rot:%x)\n"` | Room loading |
| `0x3E9710` | `"Floor Not Data!!!\n"` | Missing data error |
| `0x3E9730` | `"Dun Door Set(%d)!!!\n"` | Door placement |
| `0x3E9770` | `"Dun Way Set(%d)!!!\n"` | Corridor placement |
| `0x3E9830` | `"Room Data Nop!!!\n"` | Empty room warning |
| `0x3E9850` | `"Set Room Tbl Num(%d:%d)/(%x)!!!\n"` | Room table setup |
| `0x3E9880` | `"Room Max Over!!!\n"` | Room limit exceeded |
| `0x3E9A60` | `"Dungeon Way Model Disp Err!!!(%d)\n"` | Render error |
| `0x3E9A90` | `"Dungeon Door Model Disp Err!!!(%d)\n"` | Render error |
| `0x3E9AC0` | `"Dungeon Obj Disp Err!!!(%d)\n"` | Render error |
| `0x3E9B00` | `"Dungeon Room Disp Err!!!\n"` | Render error |
| `0x3E9DE0` | `"Treasure Get Data MAX Over!!!(Floor=%dF:ID=%d)\n"` | Chest limit |
| `0x3EA0C0` | `"Dun Trap Model Set(%d)!!!\n"` | Trap placement |
| `0x3EA1C0` | `"Trap Set(TrapNo:%d / Lv:%d)!!!\n"` | Trap init |
| `0x3EA210` | `"Map Init!!!\n"` | Automap init |
| `0x3EB8A0` | `"Wall Break Work Cut!!!\n"` | Destructible wall |
| `0x3EC4D0` | `"CockpitImg Init!!!\n"` | HUD init |
| `0x3EC820` | `"RandDungeon Set Block!!!(%d)\n"` | Random dungeon |
| `0x3EC840` | `"RandDungeon Max Over!?(%d)\n"` | Random dungeon limit |
| `0x3EC860` | `"RandDungeon GetMax Over!?(%d)\n"` | Random dungeon limit |
| `0x3EC880` | `"RandomDungeon Set(%d)!!!!!\n"` | Random dungeon init |
| `0x3EC8A0` | `"RandomDungeon Pattern!!!(%ld)!!!\n"` | Random layout |
| `0x3EC8D0` | `"Random Room Set(%d)\n"` | Random room placement |
| `0x3EC8F0` | `"Random Room Boss Exit Set(%d)\n"` | Boss room exit |
| `0x3F3634` | `"*   壁イベントデータ作成エラー   *\n"` | Wall event data error (SJIS) |
| `0x3F3660` | `"WallEventRead : FCD_wallevent\n"` | Wall event loading |
| `0x3FCA30` | `"TMLogo DungeonDataLoadEnd LastMem = (%x)\n"` | Memory debug |
| `0x3FCC80` | `"TMLogo DungeonSVDataLoadEnd LastMem = (%x)\n"` | Save data debug |

---

## Conclusion

**Zero actionable items for dungeon/exploration text in the EXE.**

All player-visible dungeon text is sourced from:

| Text Type | Source | Status |
|-----------|--------|--------|
| Floor names/descriptions | R48 MSG resource | Translated |
| Dungeon interaction messages | R49 MSG resource | Translated |
| Trap trigger messages | R49 MSG resource | Translated |
| Door/switch prompts | R49 MSG resource | Translated |
| Compass directions (N/S/E/W) | Cockpit HUD texture | Texture issue, not EXE |
| Floor indicator (B1F etc.) | Cockpit HUD rendering | Likely texture or runtime |
| Automap | Procedural rendering | No text involved |

The EXE's dungeon system uses ASCII internal identifiers (room IDs, model names, event
keys) that are never shown to players. All debug strings are TTY-only printf output.
