# Text Line Wrapping and Dialogue Box Research

## 1. How Line Breaks Work

Messages use `0xFFFE` (BE uint16) as a line break delimiter within messages, and `0xFFFF` as the message terminator. In the decoded text dump (`data/full_decoded_text.txt`), these appear as ` / ` separators between line segments.

The game does NOT auto-wrap text. All line breaks are pre-inserted as explicit FFFE tokens in the binary MSG data. The game renderer simply advances to the next line when it encounters FFFE.

## 2. Characters Per Line -- Measured from Decoded Text

### Typical NPC dialogue (Resources 40-45): 9-15 chars per line

Examples from Resource 44 (Automata shop) show tight 12-13 char lines:
```
"宝からの報酬獲得に対する"     = 12 chars
"解消力、獲得系騎法に対す"     = 12 chars  
"る効果をアップさせます。"     = 12 chars
"決して迷切らない友であり"     = 11 chars
"忠実な戦士です。"             = 8 chars
"騎法団を投入することで、"     = 11 chars
"オートマターをパワーアッ"     = 12 chars  <-- word broken mid-syllable!
"プすることができます。"       = 10 chars
```

Note: line 7 in Resource 44 breaks "パワーアップ" (power-up) across two lines at exactly 12 characters: "パワーアッ / プする". This is strong evidence that the **maximum line width is 12 or 13 full-width characters**.

### Bulletin board posts (Resource 46): up to 19 chars per line

```
"この度、ドゥーハン器民のみなさまが"     = 17 chars
"っていう依頼を出してたミリィですけど、" = 19 chars
"もうあれはいいです。"                     = 10 chars
"騎法団をくれる人が異で見つかって"         = 15 chars
```

Resource 46 is the bulletin board -- these may use a **different text box** with a wider display area than the standard NPC dialogue box.

### Shop/menu dialogue (Resource 45): 12-14 chars per line

```
"オダのうつくしいこころで"     = 12 chars
"オメェの使いをといて"         = 10 chars
"アルバイトを雇うってのは"     = 12 chars
"なんだか店っぽくて"           = 9 chars
```

### Dungeon examination text (Resource 49): up to 18 chars per line

```
"柵に何らかの装置がしかけられている" = 16 chars
"目の前にがい骨が転がっている"       = 13 chars
```

These appear in a different context (dungeon text popup), likely using a wider text area.

## 3. Maximum Characters Per Line

**Standard NPC dialogue box: ~12-13 full-width Japanese characters**

Evidence:
- Resource 44 consistently wraps at 12 characters, even breaking words mid-syllable ("パワーアッ" / "プする")
- Resources 40-45 (town NPC dialogues) rarely exceed 13 characters per line
- The screenshot `ss_Firstdialogue.png` shows 3 lines fitting in the dialogue box, with the longest being ~14 chars

**Bulletin board / dungeon text: ~18-19 characters**

Resource 46 (bulletin board) and Resource 49 (dungeon) use wider text areas, allowing up to 19 characters per line.

## 4. Pixel Width Calculation

### Font atlas: 12x12 pixel cells
- Resource 1272 is a 256x512 PSMT4 font atlas
- Grid analysis: 21 columns x 42 rows = 882 slots (matches ~858 used glyphs)
- **Cell size: 12x12 pixels**
- No variable-width glyph table found in the EXE -- this is a fixed-width font

### Standard dialogue box width
- 12 chars x 12px = **144 pixels** of text area
- 13 chars x 12px = **156 pixels** of text area

### Bulletin board / dungeon width  
- 19 chars x 12px = **228 pixels** of text area

### For English text at 12px fixed width
- If English glyphs are also 12px wide (same cell size in the font atlas): **same number of characters per line**
- Standard dialogue: 12-13 English characters per line
- Bulletin board: 18-19 English characters per line

## 5. English Text Impact Analysis

### The core problem: information density

Japanese full-width characters carry much more information per character than English letters:
- Japanese: "回復の魔石" (5 chars) = "Recovery Magic Stone" (20 chars)
- Japanese: "宝箱を開けますか？" (9 chars) = "Open the treasure chest?" (24 chars)
- Japanese: "所持金が不足しています" (11 chars) = "Insufficient funds" (18 chars)

At 12px fixed width, English words that took 5 Japanese characters now need 15-20 English characters. With only 12-13 characters per line, this means:
- **"Open the trea" / "sure chest?"** -- broken mid-word
- **"Insufficient " / "funds"** -- just barely fits in 2 lines instead of 1
- **"Recovery Magi" / "c Stone"** -- broken mid-word

### Will we need to re-wrap text? YES, absolutely.

Every translated message will need new FFFE line break positions because:
1. English text is 2-4x longer in character count than Japanese for the same meaning
2. English cannot be broken mid-word (unlike Japanese which can break anywhere)
3. The original FFFE positions are based on Japanese character counts

### Translation approach must include a line-wrapping step:
1. Translate the full message (ignoring existing FFFE positions)
2. Re-wrap the English text to fit within the character-per-line limit
3. Insert new FFFE tokens at word boundaries
4. Handle overflow (text that needs more lines than original)

## 6. Can We Use More Than 3 Lines?

### What the data shows

The standard NPC dialogue box (screenshots) shows **3 lines of text**. Most messages in Resources 40-45 have exactly 3 FFFE-delimited segments (3 lines).

However, **Resource 46 (bulletin board)** has messages with **7-9 line segments**:
```
MSG 1: 7 lines (bulletin board announcement)
MSG 2: 8 lines (quest withdrawal notice)  
MSG 3: 5 lines (mystery key discussion)
MSG 4: 6 lines (help wanted ad)
MSG 7: 9 lines (dungeon exploration story)
```

This means the game engine **already supports scrolling or paging** for longer text. The bulletin board likely uses a scroll or page-advance mechanism to display more than 3 lines.

### Empty lines as page breaks

In multi-page messages, an empty segment (just whitespace between two `/` markers) appears to signal a **page advance** -- the player presses a button and the next set of 3 lines appears:

```
MSG 1: line1 / line2 / line3 / [EMPTY] / line4 / line5 / line6 /
                                  ^-- page break here
```

This pattern is consistent: the empty segment `  ` appears after every 3rd line in the long messages.

### Can we add more FFFE breaks to split English text across more pages?

**Yes, with caveats:**
1. The page-break mechanism (empty FFFE segment) already exists -- we can use it
2. A 3-line English message that expands to 6 lines could be split: 3 lines + page break + 3 lines
3. The MSG binary format has no fixed limit on FFFE count per message
4. However, this changes the player experience: text that was one page in Japanese becomes two pages in English, requiring an extra button press

### Recommended strategy for the translation pipeline

1. **Keep 12-13 chars per line** (matching the dialogue box width)
2. **Use concise English** to minimize line count expansion
3. **Use page breaks** (empty FFFE segment) when text overflows 3 lines
4. **Write a word-wrapping function** that:
   - Takes a translated English string
   - Splits at word boundaries to fit within the per-line character limit
   - Inserts FFFE at each line break
   - Inserts an empty FFFE segment every 3 lines as a page break
5. **Consider half-width font**: If the font atlas is replaced with half-width Latin glyphs (6px per character instead of 12px), we get 24-26 chars per line, which dramatically reduces the wrapping problem

## 7. Half-Width Font Option (Critical Path)

The most impactful decision is whether to use:

**Option A: Full-width 12px English glyphs** (same cell size as Japanese)
- 12-13 chars per line
- Severe wrapping problems, many multi-page messages
- Much more page-break button presses for the player
- Simple to implement (just replace glyphs in the atlas)

**Option B: Half-width 6px English glyphs** (two English chars per Japanese cell)
- 24-26 chars per line
- Much better for English text, minimal wrapping issues
- Requires modifying the font renderer in the EXE or using a special encoding
- Complex to implement

**Option C: Variable-width rendering**
- Best visual result, natural spacing
- Requires significant EXE patching to add variable-width font support
- No existing width table in the game (confirmed by impl09-all-fonts findings)
- Most complex option

## Summary

| Parameter | Standard Dialogue | Bulletin Board | Dungeon Text |
|-----------|------------------|----------------|--------------|
| Max chars/line | 12-13 | 18-19 | 16-18 |
| Pixel width | 144-156 px | 216-228 px | 192-216 px |
| Lines visible | 3 | 3 (paged) | 2 |
| Page support | Yes (empty FFFE) | Yes | Unknown |
| English chars at 12px | 12-13 | 18-19 | 16-18 |
| English chars at 6px | 24-26 | 36-38 | 32-36 |

**Key conclusions:**
1. Line breaks are explicit FFFE tokens -- we MUST re-wrap all translated text
2. Max ~12-13 full-width chars per line in the main dialogue box
3. At 12px fixed width, English fits the same character count -- but needs 2-4x more chars per word
4. The game already supports multi-page text via empty FFFE page breaks
5. A word-wrapping utility is a required part of the translation pipeline
6. Half-width (6px) English font would dramatically reduce the wrapping problem and should be investigated as a priority
