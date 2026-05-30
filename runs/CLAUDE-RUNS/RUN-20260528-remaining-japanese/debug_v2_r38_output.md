# Debug: v2 Pipeline R38 Output Analysis
Date: 2026-05-28

## Binary File
- Path: `build/packdata_resources/0038_type01.raw`
- Size: 10,240 bytes (5 sectors)

## Sub-Header (16 bytes, LE u32 x 4)
| Field          | Value              |
|----------------|--------------------|
| h_zero1        | 0x00000000         |
| h_payload_size | 8304 (0x00002070)  |
| h_stride       | 16 (0x00000010)    |
| h_zero2        | 0x00000000         |

Payload spans bytes 16..8320. Remaining 1920 bytes are zero-padding to sector boundary.

## Offset Table
- Starts at byte 16 (no sequential table -- first u32 != 1)
- Format: BE u16 pairs (value, flags)
- Entry[0]: count=188, flags=0x0000
- Entries 1..188: message offsets (payload-relative byte offsets)
- Entry[188]: flags=0xFFFF (last marker)
- Table size: 756 bytes (189 x 4)

**RESULT: ALL 188 offsets correctly point to their corresponding FFFF-group start positions. No offset table errors.**

## Glyph Stream
- Starts at byte 772 (0x0304)
- Ends at byte 8320 (payload_end)
- Total FFFF-delimited groups: 188 (matching offset table count)
- Total FFFE line breaks: 314
- Control codes (FB00+): NONE found

## Translation Verification vs chunk_r38_fix.json

The fix file has 188 entries covering messages 0-187 (full range, no gaps).

### Summary
| Category            | Count |
|---------------------|-------|
| Correct matches     | 130   |
| Word-wrap mismatches| 29    |
| Skipped (identity)  | 29    |

### Identity Translations (29 entries -- skipped by pipeline, original data preserved)

These entries have japanese == english (already in Latin script in the original game).
The pipeline correctly skips them, preserving the original binary data unchanged.

Messages: 0 (hp), 35-36 (spaces), 159-176, 178-183, 185-187

### Word-Wrap Mismatches (29 entries)

All 29 "mismatches" are caused by the `encode_text()` word-wrapper inserting FFFE
line breaks at the 18-character limit. The translation text itself is correct --
only the line-break positions differ from what the fix file's " / " markers specify.

The fix file uses " / " to mark intended line breaks, but `encode_text()` with
`max_chars_per_line=18` re-wraps text to fit the display width, adding additional
FFFE breaks when a line segment exceeds 18 characters.

Example -- msg[87]:
- Fix file:  `bores easily. return / to town often. /`
- Binary:    `bores easily. / return / to town often. /`
  - "bores easily. return" = 20 chars, exceeds 18, so encode_text wraps after "easily."

Example -- msg[99]:
- Fix file:  `obsessed with traps. / crushed by success. /`
- Binary:    `obsessed with / traps. / crushed by / success. /`
  - "obsessed with traps." = 20 chars, gets wrapped

This is EXPECTED BEHAVIOR from the word-wrapping system. The translations are correct;
the display layout may differ slightly from the fix file's intended breaks.

### Affected messages (word-wrap differences)
87, 89, 91, 95, 99, 100, 101, 102, 103, 104, 108, 110, 111, 112, 113, 114, 115,
119, 130, 131, 132, 135, 137, 138, 140, 141, 142, 145, 147

## Bug Found: msg[149] Translation Error in chunk_r38_fix.json

The fix file has a DATA ERROR (not a pipeline error):

| Message | Japanese        | English (fix file) | Should be          |
|---------|-----------------|--------------------|--------------------|
| 148     |善「g」          | good "g"           | CORRECT            |
| 149     | 中立「n」        | good "g"           | neutral "n"        |

msg[149] is the Japanese for "neutral" but the fix file incorrectly maps it to
`good "g"` -- a copy-paste error from msg[148]. The binary faithfully encodes
what the fix file says, so the pipeline is working correctly but the input data
is wrong.

## Typo Corrections Working

Three entries fix original Japanese-side typos in already-English text:
- msg[164]: "clurelty" -> "cruelty" (CORRECT in binary)
- msg[166]: "dengerous" -> "dangerous" (CORRECT in binary)
- msg[184]: "norble" -> "noble" (CORRECT in binary)

## New Text Insertions (empty japanese slots)

13 entries inject new English text into previously empty message slots:
- msg[25-26]: lv.6, lv.7
- msg[27-28]: male, female
- msg[150-158]: alignment labels (good/neutral/evil variants)

All verified present and correct in the binary.

## Conclusions

1. **Offset table: CORRECT** -- All 188 offsets point to the right message groups.
2. **Message indexing: CORRECT** -- No message index mismatches or skipped messages.
3. **Control codes: N/A** -- R38 has no FB00+ control codes (stat/UI labels don't use them).
4. **FFFE line breaks: CORRECT** -- All " / " markers properly encoded as 0xFFFE.
5. **Word-wrapping: WORKING AS DESIGNED** -- 29 messages have extra line breaks from the
   18-char word wrapper. This is cosmetic, not a data corruption issue.
6. **DATA BUG in fix file**: msg[149] says "good \"g\"" but should say "neutral \"n\"".
   This needs to be fixed in `chunk_r38_fix.json`.
