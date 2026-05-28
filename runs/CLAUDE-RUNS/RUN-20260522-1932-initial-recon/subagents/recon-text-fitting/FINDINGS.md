# Text Fitting Analysis: Will English Translations Fit In-Place?

## Bottom Line

**No -- not all resources can fit English text in-place.** 5 out of 16 MSG resources (34-49) would overflow their sector-padded allocation. The remaining 11 have sufficient padding. Resource resizing or reallocation will be needed for the overflowing resources.

---

## Expansion Ratio Statistics

Measured across 791 translated message pairs (Japanese decoded text vs English translation):

| Metric  | Value  |
|---------|--------|
| Average | 2.12x  |
| Median  | 1.94x  |
| Minimum | 0.65x  |
| Maximum | 8.50x  |

### Distribution of Expansion Ratios

```
0.0-0.5x:    0 messages
0.5-1.0x:   23 messages  (English shorter than Japanese -- rare)
1.0-1.5x:  157 messages
1.5-2.0x:  231 messages  << peak
2.0-2.5x:  163 messages
2.5-3.0x:   92 messages
3.0-3.5x:   57 messages
3.5-4.0x:   29 messages
4.0-4.5x:   21 messages
4.5x+   :   18 messages  (extreme -- short JP items with long EN names)
```

The typical expansion is ~2x, meaning English text uses roughly twice as many characters as Japanese for the same meaning. Since each character = 2 bytes (BE uint16 glyph index), English glyph data is roughly double the size.

---

## Resources 34-49: Detailed Fitting Analysis

Each resource in PACKDATA.DIG has:
- **Payload size**: actual data bytes (extracted file size)
- **Allocated size**: sector_count * 2048 bytes (minus 16-byte header)
- **Padding**: allocated - payload (free space within the sector allocation)

```
 Res  Msgs     JA     EN  Ratio  Payload    Alloc   Padding    Pad%   Expand  NewSize   Status
  34    29    172    563   3.27      972    69616    68644  7062.1%      782     1754       OK
  35    23    140    296   2.11      524     4080     3556   678.6%      312      836       OK
  36   156   1052   1545   1.47     3390     4080      690    20.4%      986     4376  OVERFLOW +296
  37    18    383    726   1.90     2908     4080     1172    40.3%      686     3594       OK
  38   177   3135   6270   2.00*    7512     8176      664     8.8%     6270    13782  OVERFLOW +5606
  39    84    726   1443   1.99     2462    26608    24146   980.7%     1434     3896       OK
  40    55    818   1661   2.03     2034     4080     2046   100.6%     1686     3720       OK
  41    17    472    954   2.02     1000     2032     1032   103.2%      964     1964       OK
  42    13    266    605   2.27      614     2032     1418   230.9%      678     1292       OK
  43    26    415    830   2.00*    1416     2032      616    43.5%      830     2246  OVERFLOW +214
  44    57    956   1607   1.68     2306     4080     1774    76.9%     1302     3608       OK
  45   191   2718   5409   1.99     6950     8176     1226    17.6%     5382    12332  OVERFLOW +4156
  46     7    782   1474   1.89    18740    22512     3772    20.1%     1384    20124       OK
  47    30    272    681   2.50     1962     4080     2118   108.0%      818     2780       OK
  48   107    663   1326   2.00*    2186     4080     1894    86.6%     1326     3512       OK
  49   109   1299   3167   2.44     3458     4080      622    18.0%     3736     7194  OVERFLOW +3114
```

\* = 2.0x estimated (no actual translations yet for this resource)

---

## Overflow Details

### 5 Resources That Will NOT Fit In-Place

| Resource | Content | Overflow | Needs | Has Now | Fix Needed |
|----------|---------|----------|-------|---------|------------|
| 36 | Character stats/battle UI labels | +296 bytes | 4376 | 4080 | +1 sector |
| 38 | Spell/skill names (no translations yet) | +5606 bytes | 13782 | 8176 | +3 sectors |
| 43 | NPC dialogue (no translations yet) | +214 bytes | 2246 | 2032 | +1 sector |
| 45 | Vigger Shop dialogue | +4156 bytes | 12332 | 8176 | +3 sectors |
| 49 | Dungeon/story text | +3114 bytes | 7194 | 4080 | +2 sectors |

### 11 Resources That DO Fit In-Place

Resources 34, 35, 37, 39, 40, 41, 42, 44, 46, 47, 48 all have enough sector padding to absorb the English text expansion without any changes to the PACKDATA.DIG TOC.

Notable comfortable fits:
- **Res 34** (items): 7062% padding -- massive allocation, trivially fits
- **Res 39** (skills?): 981% padding -- 13x the needed space
- **Res 42** (Inn dialogue): 231% padding
- **Res 47** (quest text): 108% padding
- **Res 41** (Church dialogue): 103% padding -- just barely 2x the payload

---

## Key Observations

1. **Sector alignment creates variable padding.** Resources are stored at sector boundaries (2048 bytes). Small resources in a 1-sector allocation get large padding percentages; large resources that nearly fill their sectors get very little.

2. **Resources 38 and 43 have no translations yet.** Their overflow estimates use the average 2.0x ratio. Actual overflow could be larger or smaller depending on final translations.

3. **Resource 45 (Vigger Shop) is the worst case among translated resources.** It has 191 messages of shop dialogue that expand to nearly double, but only 17.6% padding (1226 bytes free vs 5382 bytes needed).

4. **Resource 49 has high expansion (2.44x).** Its 109 messages of dungeon/story text are particularly wordy in English, combining with tight 18% padding for a large overflow.

5. **Resource 36 is the smallest overflow.** Only 296 bytes over -- less than one sector. Could potentially be solved by shortening a few translations.

---

## Mitigation Strategies

### Option A: Resize Sector Allocations in PACKDATA.DIG TOC
Modify the TOC entries for overflowing resources to allocate more sectors. This requires:
- Shifting all subsequent resources forward in the file
- Updating all TOC sector_offset values after the modified entry
- Risk: could break if the game validates file structure

### Option B: Relocate Overflowing Resources
Move overflowing resources to unused space at the end of PACKDATA.DIG:
- Change their TOC sector_offset to point to appended data
- Simpler than shifting everything -- only modified entries need updating
- The file grows slightly but layout of other resources is untouched

### Option C: Shorten Translations
For resource 36 (only +296 bytes over), shortening translations by ~148 characters total would eliminate the overflow. This is feasible for UI labels.
For resources 38, 45, 49 the overflows are too large (3000-5600 bytes) to solve by shortening alone.

### Option D: Abbreviation + Compression
Use shorter English text where possible, plus potentially implement a simple text compression scheme. However, the glyph-index format makes compression non-trivial.

### Recommended Approach
**Option B (relocate)** for resources 38, 45, 49 (large overflows) combined with **Option C (shorten)** for resource 36 (marginal overflow). Resource 43 (+214 bytes) could go either way -- shortening ~107 characters of translations or relocating.

---

## Files

- Analysis script: `runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon-text-fitting/analyze_fitting.py`
- Full results JSON: `runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon-text-fitting/fitting_results.json`
- Source data: `data/full_decoded_text.json`, `data/translations_*.json`
- PACKDATA TOC: `extracted/PACKDATA.DIG` (12-byte entries: sector_offset, sector_count, type_code)
