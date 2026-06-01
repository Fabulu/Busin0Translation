# Chargen RAM Analysis: PACKDATA Resources Loaded During Character Creation

**Save state:** `RAMdumps/27-5.p2s` (chargen screen)
**RAM dump:** `eeMemory.bin` (32 MB PS2 EE RAM)
**Method:** Searched first 32 bytes of each resource (indices 0-2880) in the full 32MB RAM. Resources sharing identical headers were disambiguated by verifying match depth.

---

## Summary

| Metric | Count |
|--------|-------|
| Total resources scanned | 2881 |
| Unique RAM addresses with loaded resources | 45 |
| Resource indices matched (incl. duplicates from shared headers) | 68 |
| Patched (type02) resources found in RAM | 2 (R2588, R2589) |
| Patched resources running OUR translation | **0** |
| Kanji font pages (R1269-R1276) in RAM | **0** (not loaded during chargen) |
| Chargen text resources (R1187-R1195) in RAM | Only R1191 (type03 structural data) |

---

## Key Finding: Patches Not Active

**R2588** and **R2589** are the only patched resources found in RAM. Both contain the **ORIGINAL** game data, not our translations:

| Resource | RAM Address | Diffs vs Original | Diffs vs Patched |
|----------|------------|-------------------|------------------|
| R2588 | 0x01079880 | 18 bytes (runtime fixups) | 3654 bytes |
| R2589 | 0x010818C0 | 18 bytes (runtime fixups) | 3654 bytes |

The 18-byte differences from original are runtime pointer fixups by the game engine, not our patches. This confirms **the game is loading from the unmodified ISO/PACKDATA, not our patched build.**

---

## Chargen Priority Range: R1185-R1195

| Index | Type | Size | In RAM? | Notes |
|-------|------|------|---------|-------|
| R1185 | type08 | 446 KB | NO | 3D model/animation data |
| R1186 | type20 | 997 KB | NO | Large asset, likely texture atlas |
| R1187 | type02 | 401 KB | NO | MSG text resource - NOT loaded as raw blob |
| R1188 | type01 | 528 KB | NO | Font/glyph data |
| R1189 | type02 | 67 KB | NO | MSG text resource |
| R1190 | type01 | 6 KB | NO | Small lookup table |
| R1191 | type03 | 4 KB | YES @ 0x00DC3E80 | Structural/script data |
| R1192 | type02 | 157 KB | NO | MSG text resource |
| R1193 | type02 | 6 KB | NO | MSG text resource (HAS PATCH) |
| R1194 | type02 | 8 KB | NO | MSG text resource (HAS PATCH) |
| R1195 | type02 | 2 KB | NO | MSG text resource |

**Conclusion:** The chargen text resources (R1187, R1189, R1192-R1195) are NOT found as raw blobs in RAM. The game engine likely:
1. Reads them from disc into a temporary buffer
2. Parses the MSG format and extracts individual messages
3. Discards or overwrites the raw resource data

This means searching for raw resource headers won't find parsed text data.

---

## Kanji Font Pages: R1269-R1276

**None found in RAM.** These are loaded on-demand when kanji text needs rendering, and are not resident during chargen. The game likely streams font pages from disc as needed.

---

## All Resources Found in RAM (45 unique locations)

### Low Memory Region (0x00D6-0x00FF) - Game Engine / Core Data

| RAM Address | Resource(s) | Type | Size | Notes |
|-------------|------------|------|------|-------|
| 0x00D6D540 | R2098 | type05 | 301 KB | |
| 0x00DB6E80 | R1910 | type02 | 36 KB | |
| 0x00DB8C90 | R2087/2088/2089/2096/2097 | type01 | 4-14 MB | Shared header, likely large model/texture banks |
| 0x00DC1700 | R1892 | type20 | 8 KB | |
| 0x00DC3E80 | R1191 | type03 | 4 KB | Chargen structural data |
| 0x00DC7100 | R32 | type02 | 6 KB | System message table |
| 0x00DC8940 | R33 | type01 | 4 KB | |
| 0x00DCB6C0 | R28/R922 | type02 | 18 KB | Duplicate resources (identical data) |
| 0x00DD4700 | R1054/R1359 | type02 | 36 KB | Duplicate resources (identical data) |
| 0x00DDD740 | R1360 | type02 | 36 KB | |
| 0x00DE6780 | R1361 | type02 | 36 KB | |
| 0x00DEF7C0 | R1362 | type02 | 36 KB | |
| 0x00DF8800 | R1363 | type02 | 40 KB | |
| 0x00E02840 | R1364 | type04 | 71 KB | |
| 0x00E29900 | R39 | type15 | 26 KB | |
| 0x00E30140 | R1368 | type62 | 299 KB | |
| 0x00E79180 | R1358 | type02 | 34 KB | |
| 0x00E819C0 | R2157 | type17 | 53 KB | |
| 0x00E8EA00 | R2159 | type32 | 280 KB | |
| 0x00ED3240 | R29/R923 | type02 | 266 KB | Duplicate resources |
| 0x00F14280 | R30/R924 | type02 | 825 KB | Duplicate resources |
| 0x00FDDAC0 | R31/R925 | type02 | 321 KB | Duplicate resources |

### High Memory Region (0x0102-0x012B) - Active Scene Data

| RAM Address | Resource(s) | Type | Size | Notes |
|-------------|------------|------|------|-------|
| 0x0102C300 | R2155 | type10 | 274 KB | |
| 0x01071F00 | R2123/2552/2558/2562-2569/2586/2638 | type01 | 2 KB each | Small type01 with shared header |
| 0x010727C0 | R1897/1898/1899 | type06 | 8 KB | Shared header |
| 0x01075040 | R2587 | type02 | 18 KB | |
| 0x01079880 | **R2588** | type02 | 32 KB | **HAS PATCH - RAM=ORIGINAL** |
| 0x010818C0 | **R2589** | type02 | 34 KB | **HAS PATCH - RAM=ORIGINAL** |
| 0x0108A100 | R2601 | type05 | 4 KB | |
| 0x0108B140 | R2603 | type02 | 6 KB | |
| 0x0108C980 | R2608 | type02 | 16 KB | |
| 0x010909C0 | R2604 | type02 | 6 KB | |
| 0x01092200 | R2592/R2606 | type04 | 18/8 KB | |
| 0x01094240 | R2580 | type03 | 20 KB | |
| 0x0109AD40 | R47 | type03 | 4 KB | |
| 0x010A4DC0 | R1161 | type01 | 73 KB | |
| 0x010B6E00 | R1175 | type104 | 69 KB | |
| 0x010C7E40 | R1156 | type02 | 28 KB | |
| 0x010CEE80 | R1157 | type02 | 26 KB | |
| 0x010D56C0 | R1158 | type02 | 24 KB | |
| 0x010DB700 | R1159 | type02 | 28 KB | |
| 0x010E2740 | R1160 | type19 | 256 KB | |
| 0x01135C80 | R2138 | type29 | 1.5 MB | Large resource, possibly 3D scene |
| 0x012AE4C0 | R2139 | type15 | 6 KB | |
| 0x012B2DC0 | R1951 | type02 | 337 KB | |

---

## Type02 (MSG Text) Resources Loaded During Chargen

These are the type02 resources confirmed present in RAM. Cross-referenced with our patch set:

| Index | Size | RAM Address | Has Patch? |
|-------|------|------------|------------|
| R28 | 18 KB | 0x00DCB6C0 | No |
| R29 | 266 KB | 0x00ED3240 | No |
| R30 | 825 KB | 0x00F14280 | No |
| R31 | 321 KB | 0x00FDDAC0 | No |
| R32 | 6 KB | 0x00DC7100 | No |
| R1054 | 36 KB | 0x00DD4700 | No |
| R1156 | 28 KB | 0x010C7E40 | No |
| R1157 | 26 KB | 0x010CEE80 | No |
| R1158 | 24 KB | 0x010D56C0 | No |
| R1159 | 28 KB | 0x010DB700 | No |
| R1358 | 34 KB | 0x00E79180 | No |
| R1359 | 36 KB | 0x00DD4700 | No |
| R1360 | 36 KB | 0x00DDD740 | No |
| R1361 | 36 KB | 0x00DE6780 | No |
| R1362 | 36 KB | 0x00DEF7C0 | No |
| R1363 | 40 KB | 0x00DF8800 | No |
| R1910 | 36 KB | 0x00DB6E80 | No |
| R1951 | 337 KB | 0x012B2DC0 | No |
| R2587 | 18 KB | 0x01075040 | No |
| **R2588** | 32 KB | 0x01079880 | **Yes (ORIGINAL in RAM)** |
| **R2589** | 34 KB | 0x010818C0 | **Yes (ORIGINAL in RAM)** |
| R2603 | 6 KB | 0x0108B140 | No |
| R2604 | 6 KB | 0x010909C0 | No |
| R2608 | 16 KB | 0x0108C980 | No |

---

## Implications

1. **The save state was made from an unpatched ISO.** R2588 and R2589 contain original data, confirming patched PACKDATA was not used for this game session.

2. **Chargen MSG text (R1187, R1192-R1195) is not found as raw blobs.** The game parses these resources and stores parsed message data elsewhere. To find the actual rendered text, we would need to search for parsed MSG glyph sequences rather than raw resource headers.

3. **Kanji font pages are demand-loaded.** R1269-R1276 are not resident during chargen, confirming font streaming behavior.

4. **R1156-R1159 are loaded** -- these are type02 MSG resources in the 1156-1159 range that we have NOT patched yet. They may contain chargen-relevant text.

5. **R1358-R1363 are loaded** -- another block of type02 MSG resources present during chargen. R1347-R1355 from our patch set are NOT loaded (they likely belong to different game scenes).

6. **R28-R31 (system messages) are always loaded** -- these large type02 resources (6-825 KB) are core game text, possibly item/spell names and system strings. None are patched.
