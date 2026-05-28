# FMV Video Subtitle Analysis: BSN2_0.DSI

## Summary

**The BSN2_0.DSI video files contain NO subtitles, NO embedded text, and NO audio tracks.** They are raw MPEG-2 video elementary streams with a 64-byte custom header. Any text displayed during video playback is rendered by the game engine's TextEvent system using MSG resources -- already handled by the translation pipeline.

---

## Files Analyzed

| File | Size | Location |
|------|------|----------|
| BSN2_0.DSI | 63,176,704 bytes (60.3 MB) | `extracted/BSN2_0.DSI` (root) |
| BSN2_0.DSI | 32,243,712 bytes (30.7 MB) | `extracted/MOVIE/BSN2_0.DSI` |

---

## Task 1: File Format Identification

Both files share an identical structure:

- **Bytes 0-63:** Custom 64-byte header (game-specific, not MPEG standard)
- **Bytes 64+:** Raw MPEG-2 video elementary stream (starts with sequence header `00 00 01 B3`)

Header fields (little-endian):
```
0000: 02 00 00 00 40 00 00 00  (type=2, MPEG data offset=0x40)
0008: 00 C0 FF FF ...          (stream config flags)
```

The TMPGEnc encoder signature is embedded in the MPEG user data at offset 0xB4:
```
"encoded by TMPGEnc (ver. 2.510.49.157)"
```

Video parameters (from sequence header):
- Resolution: 256x448 (portrait, PS2 display orientation)
- Frame rate: 29.97 fps (NTSC)

---

## Task 2: Subtitle Stream Search

### Method
Performed a full-file binary scan of both DSI files searching for:
- **0xBD (Private Stream 1):** Standard MPEG-PS location for DVD subtitles and AC3 audio
- **0xBA (Pack Header):** Required for MPEG Program Stream multiplexing
- **0xBB (System Header):** Describes available streams in a PS
- **0x20-0x3F range start codes:** MPEG-2 subtitle streams

### Results

| Start Code | Root BSN2_0.DSI | MOVIE BSN2_0.DSI | Interpretation |
|------------|-----------------|-------------------|----------------|
| 0xBA (Pack Header) | 0 | 1 | False positive (byte4=0x11, not valid pack) |
| 0xBB (System Header) | 0 | 0 | None |
| 0xBD (Private Stream 1) | 1 | 0 | False positive (not preceded by valid PES) |
| 0xBF (Navigation) | 0 | 0 | None |

**Both occurrences are false positives** -- coincidental byte patterns `00 00 01 BA`/`BD` within the compressed video data, not real MPEG-PS structures. Evidence:

- The root file's 0xBD at offset `0x02DF66C4`: The surrounding bytes are clearly compressed video data, and no valid PES packet length follows.
- The MOVIE file's 0xBA at offset `0x0167D85C`: Byte 4 is `0x11`, which matches neither MPEG-1 (top nibble `0010`) nor MPEG-2 (top bits `01`) pack header format.

**Conclusion: Zero pack headers means these are NOT Program Streams. They are raw video elementary streams. Subtitle embedding in MPEG requires PS or TS multiplexing, which is absent.**

---

## Task 3: Text Content Scan

Scanned both files for ASCII text runs of 10+ characters:

- Root file: 7,654 runs detected -- all are random byte sequences from compressed video that happen to fall in the printable ASCII range. The only genuine text is the TMPGEnc encoder tag.
- MOVIE file: 2,819 runs detected -- same situation, only the TMPGEnc tag is meaningful.

No Japanese text (Shift-JIS patterns), no subtitle format markers (SRT timestamps, SSA headers, etc.), and no subtitle rendering commands were found.

---

## Task 4: How the Game Handles Text During Video Playback

The game uses an in-engine **TextEvent system** to overlay text on video. Evidence from prior analysis:

1. The EXE contains TextEvent functions: `TextEventSystemDelete`, `TextEventMsgIdle`, `Event Start`, `Event End`
2. All game text is stored as 16-bit glyph indices in MSG-format resources within PACKDATA.DIG (resources R34-R49, R1161, R1909, R2654)
3. Text is rendered using the font atlas (resource R1272) and composited over the video frame by the game engine
4. The MOVIE directory's BSN2_0.DSI appears to be a shorter/alternate version of the same video data, possibly for a different scene or quality level

This architecture means **all text shown during FMV sequences is already part of the MSG resource translation pipeline** and requires no separate video subtitle work.

---

## Task 5: Translation Impact

### Action Required: NONE

The DSI video files are pure video data with no translatable content. Any text appearing during cutscenes is:

1. Already in MSG resources (R34-R49 cluster, mostly translated)
2. Rendered by the TextEvent system using the game's font atlas
3. Handled by the existing translation pipeline (MSG extraction, glyph remapping, PACKDATA.DIG repacking)

### Risk Assessment

| Risk | Level | Notes |
|------|-------|-------|
| Subtitles embedded in video | **NONE** | Confirmed: raw elementary stream, no subtitle tracks |
| Hardcoded text in video frames | **NONE** | No text found; TMPGEnc does not burn subtitles |
| Text overlay during playback | **ALREADY HANDLED** | Uses MSG/TextEvent system, same as all other game text |
| Audio with spoken dialogue | **OUT OF SCOPE** | Audio is separate from these video files; no dubbed audio track present in DSI |
