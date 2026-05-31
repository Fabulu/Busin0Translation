# PCSX2 Cache Investigation: Can Stale ISO Data Be Shown?

## Short Answer

**No, PCSX2 does NOT cache raw ISO sector data between runs.** When you replace an ISO file and boot it, PCSX2 reads directly from the new file. There is no persistent block-level disc cache that would serve stale sectors from a previous ISO.

However, there are several **indirect caching mechanisms** that could cause confusing behavior.

## Caches Found on This System

### 1. gamelist.cache (DOES store ISO metadata)
- **Location:** `PCSX2/cache/gamelist.cache`
- **Contains:** File paths, game serial numbers (SLPM-65378), game titles, and file size/timestamp metadata
- **Risk:** If you replace an ISO with a different-sized file, PCSX2's game list UI might show stale game info. This is cosmetic only -- it does NOT affect what data is read at runtime.
- **Fix:** Delete `gamelist.cache` or rescan the game library.

### 2. gl_programs.bin / gl_programs.idx (shader cache)
- **Location:** `PCSX2/cache/gl_programs.bin` (836 KB) + `.idx`
- **Contains:** Compiled OpenGL shader programs
- **Risk:** None for ISO data. These cache GPU shaders, not game content. Corrupted shader caches can cause visual glitches but not wrong text/data.

### 3. Save States (.p2s files)
- **Location:** `PCSX2/sstates/SLPM-65378 (AEDB8BB2).01.p2s` and `.02.p2s`
- **Risk:** **HIGH for stale data.** Save states capture the entire emulated machine state including RAM contents. If you load a save state made from an OLD ISO, all the text/data that was already loaded into PS2 RAM will be the OLD data. The game will only read new sectors from the updated ISO if it needs data not already in RAM.
- **Fix:** Do NOT use save states when testing a new ISO build. Always cold-boot the game.

### 4. GzipIsoIndexTemplate (.pindex.tmp)
- **Config setting:** `GzipIsoIndexTemplate = $(f).pindex.tmp`
- **Purpose:** Index file for gzip-compressed ISOs (.iso.gz). Stored next to the ISO file.
- **Risk:** Only relevant for compressed ISOs. Since your ISO (`Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso`) is uncompressed, this does not apply.
- **No .pindex.tmp files found** next to your ISO.

## Relevant PCSX2.ini Settings

| Setting | Value | Meaning |
|---------|-------|---------|
| `CdvdPrecache` | `false` | ISO is NOT preloaded into RAM. Sectors are read on demand. Good -- no stale preloaded data. |
| `fastCDVD` | `false` | No aggressive disc read speedhack. Good -- reads are faithful. |
| `CdvdDumpBlocks` | `false` | Block dump recording is off. No .dump files being created. |
| `EnableFastBoot` | `true` | Skips BIOS, goes straight to game. This is fine and does not cache ISO data. |
| `DisableShaderCache` | `false` | Shader cache is enabled but this only affects GPU, not disc data. |

## What Could Actually Cause "Stale" Japanese Text

Given that PCSX2 does NOT cache ISO sectors, if you see old Japanese text after building a new ISO, the cause is one of:

1. **Save state loaded** -- The #1 suspect. Any save state from before the ISO rebuild will have old text in RAM.
2. **Wrong ISO file loaded** -- PCSX2 remembers the last ISO path. If you have multiple ISOs, confirm the correct one is selected.
3. **ISO build did not actually inject the new data** -- The build script may have failed silently or patched the wrong offsets.
4. **Game re-reads data from disc at specific triggers** -- Some text may be loaded at boot, some on room entry, some on menu open. You may need to trigger the right event to see updated text.

## Recommended Testing Procedure

1. Build the new ISO
2. Verify the ISO has the patched data (e.g., hex-dump specific offsets)
3. Close PCSX2 completely
4. Delete `cache/gamelist.cache` (optional but eliminates one variable)
5. Open PCSX2, select the new ISO explicitly via File > Open
6. **Boot CDVD (Full)** or **(Fast)** -- do NOT load a save state
7. Navigate in-game to where the text should appear

## Conclusion

PCSX2 reads ISO sectors directly from disk on each boot with your current settings (`CdvdPrecache=false`, `fastCDVD=false`). The emulator does not maintain a persistent sector cache. **If you see stale text, the problem is almost certainly in save states or the ISO build itself, not in PCSX2 caching.**
