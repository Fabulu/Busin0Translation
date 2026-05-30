# R37 Chargen Prompt Overflow Analysis

## Problem
The chargen top textbox shows 4 lines instead of 3, causing overflow.

## Root Cause
Three R37 messages produce more than 3 visible lines after `clean_and_encode()`:

### msg 1 (Enter name prompt) -- 5 lines, OVERFLOW
Source: `chunk_01_translated.json` (no override exists)
```
'Enter your name. [M / name/F name: Auto- / fill] /'
```
After clean_and_encode splits on " / " and encode_text word-wraps at 18 chars:
```
line 1: "Enter your name."    (17 chars -- from part 0, fits in one line)
FFFE
line 2: "[M"                  (2 chars -- part 1 "[M" gets word-wrapped but "[M" has no space)
FFFE                          (wait -- part 1 is "name/F name: Auto-")
```
Actually the split is:
- part 0: "Enter your name. [M"  -> word_wrap -> "Enter your name." (17) + FFFE + "[M" (2) = 2 lines
- part 1: "name/F name: Auto-"   -> word_wrap -> "name/F name:" (12) + " " + "Auto-" would be 18, fits = 1 line
- part 2: "fill]"                -> 1 line
- part 3: (empty, trailing)      -> just FFFE

Total FFFE tokens: 4 (between parts) + 1 (word-wrap in part 0) = but actually encode_text handles part 0 internally.

Exact glyph stream produced:
```
Enter your name. [FFFE][M [FFFE]name/F name: Auto- [FFFE]fill] [FFFE]
```
**5 display lines = OVERFLOW (max 3)**

### msg 2 (Enter name prompt, override) -- 5 lines, OVERFLOW  
Source: `chunk_r37_r48_r49_translated.json` (overrides chunk_01 msg 2)
```
'enter a name. m / name, f name: auto- / fill /'
```
Glyph stream:
```
enter a name. m [FFFE]name, f name: [FFFE]auto- [FFFE]fill [FFFE]
```
**5 display lines = OVERFLOW (max 3)**

### msg 124 (Confirm prompt) -- 5 lines, OVERFLOW
Source: `chunk_r37_extra.json`
```
'Press O or X button / to confirm your / choices. /'
```
Glyph stream:
```
Press O or X [FFFE]button [FFFE]to confirm your [FFFE]choices. [FFFE]
```
**5 display lines = OVERFLOW (max 3)**

Note: "Press O or X button" is 20 chars, so encode_text word-wraps it into 2 lines ("Press O or X" + "button"), adding an extra FFFE.

## All R37 Chargen Prompt Messages (final after overrides)

| msg | lines | status | final text |
|-----|-------|--------|------------|
| 1   | 5     | **OVERFLOW** | `Enter your name. [M / name/F name: Auto- / fill] /` |
| 2   | 5     | **OVERFLOW** | `enter a name. m / name, f name: auto- / fill /` |
| 3   | 2     | OK     | `select gender. /` |
| 4   | 2     | OK     | `select a race. /` |
| 5   | 2     | OK     | `select alignment. /` |
| 6   | 2     | OK     | `select a class. /` |
| 7   | 3     | OK     | `allocate stat / points. /` |
| 8   | 2     | OK     | `Is this OK? /` |
| 124 | 5     | **OVERFLOW** | `Press O or X button / to confirm your / choices. /` |

## How the Pipeline Processes These

1. `build_full_english_v2.py` calls `clean_and_encode(english_text)`
2. `clean_and_encode` splits on " / " to get parts, inserting 0xFFFE between parts
3. For each non-empty part, it calls `encode_text(part, max_chars_per_line=18, max_lines_per_page=3)`
4. `encode_text` does word-wrapping at 18 chars, inserting FFFE + potentially FFD2 page breaks
5. The problem: each " / " in the translation becomes an FFFE, AND encode_text may add MORE FFFEs for word-wrap within a single part

The chargen top box only has room for 3 lines. The trailing FFFE (from trailing " /") counts as a blank line too.

## Fix Recommendations

### msg 1 -- Shorten to fit 3 lines (2 content + trailing FFFE)
Current: `Enter your name. [M / name/F name: Auto- / fill] /`
Fix: `Enter your name. / ` (single line + trailing FFFE = 2 lines, OK)
Or: `Name your hero. / ` 

The "[M name/F name: Auto-fill]" instruction is too long and not essential -- the UI buttons already show these options.

### msg 2 -- Same issue, same fix
Current: `enter a name. m / name, f name: auto- / fill /`
Fix: `Enter your name. / ` (2 lines, OK)

Note: msg 1 and msg 2 appear to be duplicates for the same prompt. msg 2 wins for the override from `chunk_r37_r48_r49_translated.json`, but msg 1 from `chunk_01_translated.json` has no override -- so BOTH are injected. The game likely uses one or the other depending on context.

### msg 124 -- Shorten to fit 3 lines
Current: `Press O or X button / to confirm your / choices. /`
Fix: `Press O/X to confirm / your choices. /` (2 content lines + trailing FFFE = 3 lines, OK)
Or: `Confirm with O or X. / ` (2 lines, OK)

## Key Constraint
Each content line must be <= 18 characters. Total visible lines (including trailing FFFE blank) must be <= 3.
So: **maximum 2 content lines + 1 trailing FFFE**, or **3 content lines with NO trailing FFFE** (but all R37 entries have trailing " /").

Effectively: **2 content lines maximum** for R37 chargen prompts.
