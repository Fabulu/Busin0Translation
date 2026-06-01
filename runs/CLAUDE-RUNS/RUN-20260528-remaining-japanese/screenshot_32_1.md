# Screenshot Analysis: Save State 32-1

## File
- Source: `RAMdumps/32-1.p2s` (extracted Screenshot.png)
- Saved to: `RAMdumps/v32_screenshots/32-1_Screenshot.png`

## Screen: Character Name Entry (New Registration)

### Element-by-Element Breakdown

#### Upper Left (Banner Area)
- Red/orange banner with Japanese text: **新規登録** (Shinki Touroku = "New Registration")
- This is STILL JAPANESE -- not translated.

#### Prompt Box (Upper Right)
- English text: **"Enter your name."**
- This IS translated (was also translated in v27 as "Enter Your Name." with different capitalization).

#### Name Field
- Italic label: **"Name"** on the left (English)
- Input field shows: **BABA___** (user has typed "BABA", 4 remaining blank slots shown as underscores)
- **Level 1** indicator on the far right

#### Character Grid (Main Input Area)
- 6 rows x 10 columns of characters:
  - Row 1: A B C D E  G H **[I]** J  (cursor highlight on I)
  - Row 2: K L  N O  P Q R S T
  - Row 3: U V W X Y Z . , ! ?
  - Row 4: a b c d e  f g h i j
  - Row 5: k l m n o  p q r s t
  - Row 6: u v w x y z  -- '
- Note: Some positions appear blank (F missing from row 1, M missing from row 2) -- likely spacing/alignment artifacts or the grid has gaps.

#### Tabs (Right Side of Grid)
- **カナ** (Katakana) -- highlighted/selected
- **かな** (Hiragana)
- **英数** (Eisuu = Alphanumeric)
- **記号** (Kigou = Symbols)
- ALL FOUR TABS ARE STILL IN JAPANESE -- not translated.

#### Bottom Area
- Two rows:
  - **M  n a 決定** -- "M" likely "Male", partially overlapping with **決定** (Kettei = "Confirm/OK")
  - **F  n a m e** -- "F" likely "Female"
- **決定** is STILL JAPANESE -- not translated.
- The "name" text next to M/F appears to be an English label but is partially obscured by the 決定 button overlay.

### Background
- Parchment/old paper texture on brown/wood background
- Decorative corner scrollwork on the dialog frame

---

## Comparison: v32 (32-1) vs v27 (27-1)

### What CHANGED (Improvements in v32)
1. **Character grid content**: v27 showed only lowercase letters (a-z repeated across 6 rows). v32 now shows BOTH uppercase (A-Z) and lowercase (a-z) properly laid out -- the grid is now correct and functional.
2. **Prompt text capitalization**: v27 had "Enter Your Name." (title case), v32 has "Enter your name." (sentence case) -- minor style fix.
3. **Name field**: v27 showed blank underscores (no name entered yet). v32 shows "BABA" partially typed -- just a different save state moment, not a code change.
4. **Gender/Confirm area**: v27 showed "L a u r 決定" and "M  n a m e". v32 shows "M  n a 決定" and "F  n a m e". The labels changed from what appeared to be a partially typed name ("Laur") to gender labels (M/F).

### What DID NOT Change (Still Japanese)
1. **新規登録** banner -- still Japanese, NOT translated
2. **カナ / かな / 英数 / 記号** tabs -- still Japanese, NOT translated
3. **決定** confirm button -- still Japanese, NOT translated

### Remaining Japanese on This Screen
| Element | Japanese | English Translation | Priority |
|---------|----------|-------------------|----------|
| Banner | 新規登録 | New Registration | HIGH |
| Tab 1 | カナ | Katakana | MEDIUM |
| Tab 2 | かな | Hiragana | MEDIUM |
| Tab 3 | 英数 | Alphanumeric | MEDIUM |
| Tab 4 | 記号 | Symbols | MEDIUM |
| Button | 決定 | Confirm / OK | HIGH |

### Assessment
The character grid is now properly populated with both upper and lowercase Latin characters (a major improvement over v27 which had duplicated lowercase rows). However, **5 UI elements on this screen remain in Japanese** -- these are likely hardcoded in the EXE or rendered via the game's native font system rather than through the MSG text injection pipeline.
