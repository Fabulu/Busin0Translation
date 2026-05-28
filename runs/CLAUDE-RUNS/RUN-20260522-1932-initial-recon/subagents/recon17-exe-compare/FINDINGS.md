# Recon 17: BUSIN 1 EXE vs BUSIN 0 EXE String Comparison

## Executive Summary

BUSIN 1 (English, SLUS_202.59, 5,038,496 bytes) is **dramatically different** from BUSIN 0 (Japanese, ~4.1MB) in terms of embedded debug strings. The English EXE has been **stripped of nearly all the debug/logging strings** present in the Japanese EXE. This is a critical finding for the translation project.

## Key Finding: Stripped Debug Strings

### BUSIN 0 (Japanese) had extensive debug infrastructure:
- **FCD_ resource names**: 32 unique references (FCD_battle_font, FCD_event_font, FCD_event_frame, FCD_wallevent, FCD_haikai, FCD_effect_mnist, FCD_game_common_effect, FCD_battle_common_effect, FCD_battle_weapon, FCD_battle_weapon_add, FCD_battle_result, FCD_death, FCD_notice_data)
- **TextEvent system**: 20+ debug strings (TextEventSystemDelete, TextEventEveAddr, TextEventMsgLinkSetCnt, TextEventMsgIdle, TextEventImageDrawRequest, etc.)
- **MessageDataLoadClose**: Present with format code
- **BattleFieldRead / BattleFieldKill / BattleFieldObjectFree**: All present
- **ItemSystemRead**: Present
- **WallEventRead**: Present
- **BSN2_0.DSI**: File reference present
- **Guild Npc Load**: Present
- **Waku (frame) system**: Multiple debug strings

### BUSIN 1 (English) - ALL OF THE ABOVE ARE ABSENT:
- **FCD_ references**: ZERO (0 found)
- **TextEvent strings**: ZERO (0 found)
- **MessageDataLoadClose**: NOT FOUND
- **BattleFieldRead/Kill**: NOT FOUND
- **ItemSystemRead**: NOT FOUND
- **WallEventRead**: NOT FOUND
- **BSN/DSI references**: NOT FOUND
- **Guild Npc strings**: NOT FOUND
- **Waku strings**: NOT FOUND
- **NPC strings**: NOT FOUND

## What BUSIN 1 DOES Have

### 1. Source File Paths (Development Artifacts)
Major discovery - BUSIN 1 contains **source code paths** not present in BUSIN 0:
```
source/game/battle/data/weapon00.dat through weapon04.dat
source/game/battle/data/protec00.dat through protec04.dat
source/game/battle/data/tool00.dat through tool04.dat
source/game/battle/data/access00.dat through access04.dat
source/game/battle/data/mate00.dat through mate04.dat
source/game/battle/data/stone00.dat through stone04.dat
source/game/battle/data/magic00.dat through magic04.dat
source/game/battle/data/allied00.dat through allied04.dat
source/game/battle/data/point00.dat through point04.dat
source/game/battle/data/output00.sav through output11.sav
source/game/battle/data/status.ssd
source/game/btl_sequence/dt_seq0.dat
```
These are **build system paths** pointing to where data files were located during development.

### 2. CD-ROM Module Paths
```
cdrom0:\IOPRP234.IMG;1
cdrom0:\SIO2MAN.IRX;1
cdrom0:\PADMAN.IRX;1
cdrom0:\MCMAN.IRX;1
cdrom0:\MCSERV.IRX;1
cdrom0:\LIBSD.IRX;1
cdrom0:\MODMIDI.IRX;1
cdrom0:\MODHSYN.IRX;1
cdrom0:\MODMSIN.IRX;1
cdrom0:\ASDMUS.IRX;1
cdrom0:\%s          (generic file loader format string)
```

### 3. BGM Music File Paths
```
\BGM\WIZB01.INT;1 through \BGM\WIZB36.VSD;1
\BGM\WIZ02SP.VSD;1
```

### 4. Memory Card / Save Data Strings
```
BASLUS-20259WIZTFL     (save file identifier - SLUS-20259 = BUSIN 1's serial)
WIZ-GBUSIN0            (save slot names)
WIZ-GBUSIN1
WIZ-GBUSIN2
WIZ-STOPPAGE           (suspend save)
DTWIZTEST              (test save?)
```

### 5. Debug Menu (Retained)
```
%Y --- DEBUG MENU ---
```
Only ONE debug reference survives in the English EXE.

### 6. English Game Data Labels (Debug Editor Strings)
The EXE contains extensive **debug editor/tool labels** in English:
- Weapon list editor: WEAPON LIST, PROTECTOR LIST, TOOL LIST, ACCESSORY LIST, MAGIC LIST
- Character stats: STRENGTH, IQ, FAITH, STAMINA, QUICK, LUCK, FEELING
- Status effects: SLEEP, POISON, PARALYZED, PETRIFIED, STAN, DEAD, SILENCE, CHAOS
- Battle debug: BATTLE SYSTEM, BATTLE PRIORITY, BATTLE STATUS, MONSTER ACTION
- Monster debug: MONSTER PARA, TRIBE, CLASS, LEVEL, AC, HP
- Equipment: BURN, COLD, THUNDER, CURSE, HAND
- Classes: FIG SAM PAR NIN THI PRI BIS MAG
- Scene editor: Scene editor, SCENE NUM
- Camera debug: CAMERA, CAM X/Y/Z/RX/RY/RZ
- Light debug: LIGHT
- Effect debug: EFFECT010-013

### 7. English Item/Equipment Category Names
At offset 0x004C2D00+:
```
FLAIL, STAFF, HANDAXE, KATANA, CHOP, STARS, STONE
ARMOR, HELMET, GLOVE, SHIELD
WEAK, NORMAL, STRONG
SCROLL, CHARM, RING, BOOTS, MANTLE, RIBBON, SPECIAL
```

### 8. Battle/Game System Strings (Simplified)
BUSIN 1 has simplified loading messages compared to BUSIN 0:
```
--- Battle Field Load ---
--- Battle Other Data Load ---
--- Battle Parameter Data Load ---
--- Battle Item Data Load ---
--- Battle BGM Load ---
--- Battle SE Load ---
--- Monster Load ---
Monster Sequence Load Done!!
WEAPON Data Load Done!!
PROTECTOR Data Load Done!!
Battle Font free
Msg No Over!!
```

### 9. Event References
```
EVENT 00 through EVENT 04
EVENT 00  [ INCUBUS/FLESHGOLEM ]
EVENT 01  [ DEATH ]
EVENT 02  [ WARGOD ]
EventData CheckSum = %d
Event Item Error : Player Name Select No
Event Dealing Error : Player Name Select No
```

### 10. Notable String: NTSC Detection
```
0x00497080: NTSC or USA!!!
```
This suggests the EXE has region detection code.

### 11. Capture/Screenshot Reference
```
0x0033FCE8: CaptureTmx/wizcap0717_0.tmx
```
A development screenshot capture path, suggesting a build date around July 17.

## Comparative Analysis

| Feature | BUSIN 0 (JP) | BUSIN 1 (EN) |
|---------|-------------|-------------|
| EXE Size | ~4.1 MB | ~4.8 MB |
| Total ASCII strings (>=4 chars) | ~11,036 | ~11,078 |
| FCD_ resource names | 32 references | 0 references |
| TextEvent debug strings | 20+ strings | 0 strings |
| MessageDataLoadClose | Present | Absent |
| BattleFieldRead/Kill debug | Present | Absent |
| ItemSystemRead | Present | Absent |
| WallEventRead debug | Present | Absent |
| Waku (frame) debug | Multiple | 0 |
| NPC/Guild debug | Present | Absent |
| BSN_0.DSI reference | Present | Absent |
| Source code paths | Absent | 87 paths (source/game/...) |
| Debug editor labels | Absent | Extensive English labels |
| Save ID | SLPS-25249 | SLUS-20259 |
| BGM paths | Similar | Similar (WIZ prefix) |
| English item names | Absent | Present |
| DEBUG MENU reference | Present (multiple) | Present (1 only) |

## Implications for Translation Project

1. **The FCD_ system still exists in BUSIN 1** - the resource loading code is present, just the debug print strings were removed. The actual FCD resource names are likely embedded in the FCD file headers on disc, not needing to be in the EXE.

2. **TextEvent system is still functional** - the code is there, just stripped of debug logging. The system still processes EVE files and MSG data the same way.

3. **BUSIN 1 is a "release build"** compared to BUSIN 0 which appears to be closer to a "debug build". The English localization team stripped debug strings but added source path references and debug editor UI labels.

4. **The source/game/battle/data/ paths** reveal the internal build structure. The game has numbered data variants (00-04) suggesting multiple difficulty levels or game versions.

5. **Save data format** uses BASLUS-20259WIZTFL identifier and WIZ-GBUSIN0/1/2 slot names, which is the same pattern as the Japanese version but with SLUS instead of SLPS.

6. **The "Msg No Over!!" string** confirms that the message system from BUSIN 0 is present in BUSIN 1, just with most debug output removed.

7. **"Battle Font free" string** confirms FCD_battle_font equivalent handling exists, matching BUSIN 0's "BattleFontKill : FCD_battle_font".

## Files

- Scanner script: `scan_exe.py`
- Full scan results: `scan_results.txt`
- BUSIN 1 EXE: `C:/Programmieren/wizardrytranslation/extracted_busin1/SLUS_202.59`
- BUSIN 0 strings reference: `C:/Programmieren/wizardrytranslation/dumps/exe_strings.txt`
