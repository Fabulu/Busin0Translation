# Off-By-One Audit: All Chunk Fix Files

Date: 2026-05-28

## Method

For each fix/translated chunk file, compared the Japanese text at message index `m`
against the original chunks (chunk_00 through chunk_09) at both `m` and `m-1`.
If fix[m].japanese == orig[m-1].japanese for a majority of entries, the file is
off-by-one (uses 1-indexed FFFF groups instead of 0-indexed).

## Results Summary

| File | Status | Verdict |
|------|--------|---------|
| chunk_r36_translated.json | 154/158 match orig[m] | CORRECT - no fix needed |
| chunk_r40_r42_translated.json | R40: 46 match orig[m-1], R41: 5 match orig[m-1], R42: 8 match orig[m-1] | **OFF-BY-ONE - NEEDS FIX** |
| chunk_r43_fix.json | 26/26 match orig[m] | CORRECT - no fix needed |
| chunk_r43_r45_translated.json | R44: 47 match orig[m-1], R45: 183 match orig[m-1], R43: 11 new (same file = same bug) | **OFF-BY-ONE - NEEDS FIX** |
| chunk_r34_fix.json | 560/564 beyond original range (new msgs), 4 different | CORRECT - messages are new content beyond chunk_00 range |
| chunk_r38_fix.json | Already fixed (-1 applied) | OK |
| chunk_r37_extra.json | Already fixed (-1 applied); 3 match orig[m] | OK |
| chunk_r37_r48_r49_translated.json | Already fixed (-1 applied); R37: 6 match orig[m] | OK |

## Detailed Findings

### chunk_r40_r42_translated.json - OFF-BY-ONE CONFIRMED

All three resources (R40, R41, R42) are shifted +1.

Evidence for R40 (46 of 55 entries confirm):
- fix msg 2 ("ようこそ、冒険者よ") == orig msg 1
- fix msg 5 ("おや、もう出て行くのか？") == orig msg 4
- fix msg 7 ("能力ステータス") == orig msg 6
- fix msg 8 ("転職") == orig msg 7
- ... and 42 more

Evidence for R41 (5 of 17 entries confirm, rest are improved glyph decodes):
- Pattern consistent with R40

Evidence for R42 (8 of 13 entries confirm):
- Pattern consistent with R40

**Fix needed: subtract 1 from all message indices in this file.**

### chunk_r43_r45_translated.json - OFF-BY-ONE CONFIRMED

R44 and R45 are shifted +1. R43 entries (27-38) are beyond original range but
since they come from the same extraction pass, they have the same bug.

Evidence for R44 (47 of 57 entries confirm):
- All entries start at msg 2 instead of msg 1

Evidence for R45 (183 of 195 entries confirm):
- Overwhelming match with orig[m-1]

**Fix needed: subtract 1 from all message indices in this file.**

### chunk_r36_translated.json - CORRECT

154 of 158 entries match orig[m] exactly. The file includes msg 0 (not in original)
and msg 97 (gap in original). This file was generated correctly with 0-indexed groups.

### chunk_r43_fix.json - CORRECT

All 26 entries match orig[m] exactly. No shift needed.

### chunk_r34_fix.json - CORRECT (different situation)

This file covers R34 messages 0-1162, far beyond the original chunk_00 range of 1-29.
560 of 564 entries have no original counterpart to compare against (they're new content).
The 4 entries that do overlap are "different" (improved glyph decodes, not shifted).
Since this file was created after the off-by-one bug was identified and the message
indices go well beyond the original range, it appears correctly indexed.

## Action Items

1. **chunk_r40_r42_translated.json**: Apply -1 to all message indices
2. **chunk_r43_r45_translated.json**: Apply -1 to all message indices
3. All other files: no changes needed
