# Diagnosis: Luna Light Bar - Green Blinking Icon

## Root Cause

**The message stream in resource 43 is corrupted by `build/build_full_english.py`** due to a message-separator mismatch between the encoder and the injector.

### The Mismatch

Resource 43 uses **two** message separators in its glyph stream:
- `0xFFFE` -- sub-message separator (87 occurrences)
- `0xFFFF` -- group separator (40 occurrences)

The translation chunks (`data/translate_chunks/chunk_04_translated.json`, `chunk_05_translated.json`) index messages using the **FFFE-based** 88-message numbering (matching the decoder in `build/decode_r43.py`). Translations target message indices 1-26.

However, the injection loop in `build/build_full_english.py` (lines 74-94) parses the stream splitting **only on `0xFFFF`**, which yields just 29 message groups. Each FFFF-group contains multiple FFFE-separated sub-messages.

When translation message 1 ("Hey there, how's that request going?") is injected at pipeline-message-1, it replaces the entire FFFF-group-1 (which was only 2 glyphs: `[0, FFFE]`). The pipeline writes English glyph IDs directly into the stream where the game expects control codes and Japanese glyph sequences.

### Why This Produces a Green Blinking Icon

Resource 43 contains a **39-entry offset table** (bytes 16-174 of the raw file) that stores byte offsets into the message stream. The offset table is preserved unchanged by the pipeline. But the message stream it points into has been restructured by the English injection:

- Original stream: `FFFF 0000 FFFE FFFF 0074 0072 ...` (Japanese glyphs with FFFE structure)
- Patched stream:  `FFFF 0077 0025 0039 0001 0034 ...` (English glyph IDs: "Hey ther...")

The offset table's entry 1 points to byte 160 in the payload (stream byte 2). In the original data, this landed at the start of a message group boundary. In the patched data, it lands in the middle of the English text "Hey there...". The game reads glyph IDs from the corrupted offset, gets values that either:
1. Point outside the glyph atlas (producing an undefined texture reference -- the green blinking icon)
2. Are misinterpreted as control codes triggering rendering artifacts

### Scope of Corruption

The same bug affects **all 21 resources** processed by `build_full_english.py`:

| Resource | Orig Size | Build Size | Delta |
|----------|-----------|------------|-------|
| 0034     | 69,632    | 28,672     | -40,960 |
| 0039     | 26,624    | 6,144      | -20,480 |
| 0046     | 22,528    | 4,096      | -18,432 |
| 1053     | 38,912    | 6,144      | -32,768 |
| 1908     | 206,848   | 2,048      | -204,800 |
| 2124     | 34,816    | 2,048      | -32,768 |
| 2654     | 184,320   | 10,240     | -174,080 |

Resources 1908, 2124, and 2654 are **not MSG-format** resources (types 06, 01, 44) but the pipeline tries to parse them as MSG anyway, destroying them.

The PACKDATA.DIG TOC has **2,847 shifted entries** because the dramatic size reductions in corrupted resources cascade sector offsets to all subsequent resources.

## Fix Required

The injection loop in `build/build_full_english.py` must be updated to:

1. **Parse messages using both `0xFFFE` and `0xFFFF`** as separators, matching the decoder's numbering scheme used by the translation chunks.

2. **Preserve the offset table** and recompute it when the stream changes size, so that the 39 offset entries still point to valid message group boundaries.

3. **Skip non-MSG resources** (types other than 01/03) that happen to have translation entries -- or at minimum, validate the resource structure before attempting to parse/rebuild the glyph stream.

### Specific Code Change Needed

In `build/build_full_english.py`, lines 74-94, the message parser currently does:
```python
if w == 0xFFFF:
    msgs.append((ms, i))
```

It must also handle `0xFFFE`:
```python
if w in (0xFFFF, 0xFFFE):
    msgs.append((ms, i))
```

And the rebuild loop must emit the correct separator for each message boundary (FFFE or FFFF), preserving the original separator structure rather than always emitting FFFF.

The same fix is needed in `build/full_patch_pipeline.py` (lines 50-66), though that script currently only processes resources 34 and 36 (from `data/encoded_translations.json`).

## Files Involved

- **Corrupting script**: `build/build_full_english.py` (lines 67-104)
- **Same bug exists in**: `build/full_patch_pipeline.py` (lines 42-77)
- **Correct decoder**: `build/decode_r43.py` (handles both FFFE and FFFF)
- **Translation data**: `data/translate_chunks/chunk_04_translated.json`, `chunk_05_translated.json`
- **Corrupted output**: `build/packdata_resources/0043_type01.raw` (payload_size 1416->1814)
- **Original resource**: `extracted/packdata_raw/0043_type01.raw` (1 sector, 1416-byte payload)

## Verification

Compare original vs patched resource 43:
- Original payload_size: 1416 bytes, 88 FFFE-messages, 40 FFFF-groups
- Patched payload_size: 1814 bytes (398 bytes larger -- the injected English text)
- First corruption byte: offset 177 (stream byte 3, where FFFE should be but English glyph 'w' was written)
- Total differing bytes: 1,074 out of 2,048
