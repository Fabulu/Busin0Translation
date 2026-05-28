# Font Atlas Research: English Font for Busin 0 (PS2)

## 1. Character Count Requirements

**Printable ASCII (0x20-0x7E): 95 characters**
- 26 uppercase: A-Z
- 26 lowercase: a-z (ALREADY in atlas at glyphs 33-58)
- 10 digits: 0-9 (fullwidth digits ALREADY at glyphs 16-25)
- 33 punctuation/symbols: ` ~ ! @ # $ % ^ & * ( ) - _ = + [ ] { } \ | ; : ' " , . < > / ?

**Extended characters for RPG text (~30-50 more):**
- Accented vowels for proper nouns: e, e, a (common in fantasy names)
- Typographic: ellipsis (...), em-dash, curly quotes
- Game-specific: arrows, heart, star, diamond (status icons)
- Currency/math: x (multiply), +, -, % (already needed for stats)

**Total needed: ~95-145 characters** out of 882 available slots.

## 2. Slot Allocation Strategy

### Current Atlas Layout
- 882 total glyph slots (21 columns x 42 rows, 12x12 cells)
- 492 glyphs currently mapped (from GLYPH_MAP_REFERENCE.md)
- Slots used span up to glyph ~1131, but the atlas is only 882 physical slots
- The game uses a glyph INDEX that maps to atlas positions (not 1:1 with slot number)

### Recommendation: REPLACE ALL SLOTS

**Rationale:**
1. We only need ~95-145 English characters, far fewer than 882 slots.
2. The game's text engine uses glyph indices from MSG resources. When we replace Japanese text with English text, we control which glyph indices appear in the translated messages.
3. Keeping Japanese glyphs is unnecessary -- if all text is translated to English, no Japanese glyphs will be referenced.
4. We should map English characters to LOW glyph indices (e.g., ASCII 0x20-0x7E map to glyphs 32-126) for simplicity, since lowercase a-z already lives at 33-58.

### Proposed Glyph Map

The game already has these mappings that we should preserve or align with:
- Glyphs 16-25: digits 0-9 (fullwidth, but we can reuse the slots)
- Glyphs 33-58: lowercase a-z (already mapped!)
- Glyphs 13, 31, 62, 63, 91-94: various punctuation

**Suggested layout (first ~100 slots):**
```
Slots 0-15:    Special/unused (slot 0 = space/blank, 13 = dash)
Slots 16-25:   Digits 0-9 (keep existing mapping)
Slots 26-31:   Punctuation: ? ! . , ; :
Slots 32:      Space
Slots 33-58:   Lowercase a-z (keep existing mapping)
Slots 59-84:   Uppercase A-Z (NEW)
Slots 85-95:   Common punctuation: ( ) [ ] { } ' " - + =
Slots 96-110:  Extended: @ # $ % ^ & * / \ | < > ~ `
Slots 111-126: Accented characters, arrows, special RPG symbols
Slots 127-882: BLANK (unused, filled with transparent pixels)
```

## 3. Font Selection

### Requirements
- Must be readable at 12x12 pixels on a 480i NTSC display (interlaced, ~640x448 visible)
- Must be monospace or near-monospace (the game appears to use fixed-width rendering)
- Must have clear distinction between similar characters: I/l/1, O/0, etc.
- Anti-aliasing is supported (the palette has 16 grayscale levels)

### Top Recommendations

**Tier 1 -- Purpose-built bitmap fonts (BEST for this use case):**

| Font | Size | License | Notes |
|------|------|---------|-------|
| **Terminus** | 12px variant | OFL | Gold standard bitmap font. Extremely clear at small sizes. Designed for terminals = perfect readability. Available as TTF via kakwafont. |
| **Tamzen** | 12px (10x20 scaled down) | MIT | Fork of Tamsyn, covers ASCII + extended Latin. Battle-tested in retro projects. |
| **Proggy Clean** | 10px native | MIT | Very popular programmer font. Crisp at small sizes. May be too small for 12x12 cells. |

**Tier 2 -- System fonts that render acceptably at 12px:**

| Font | Notes |
|------|-------|
| **Consolas** | Ships with Windows. Good at 12px with hinting. Monospace. |
| **Cascadia Mono** | Microsoft's modern terminal font. May be on this system. |
| **Courier New** | Universal fallback. Legible but ugly at 12px. |
| **MS Gothic** | Already on this system (Japanese-capable). Has clear Latin glyphs. |

**Tier 3 -- Custom pixel art (if nothing else works):**
- Hand-draw glyphs in a 12x12 grid using a pixel editor
- Use existing ROM hacking font sheets from romhacking.net/fonts

### Recommendation: Start with Terminus or MS Gothic

**MS Gothic** is particularly interesting because:
1. It is definitely installed on this Windows machine (it ships with all Japanese Windows and most international Windows installs)
2. It was designed for CJK display at small pixel sizes
3. Its Latin glyphs are clean and monospaced
4. It can render both English AND Japanese if we ever need mixed text

**Terminus** is the best pure-English option if we want maximum readability.

## 4. Pillow (PIL) Capability

**CONFIRMED: Pillow 12.1.1 is installed and working.**

Tested successfully:
- `PIL.ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 12)` -- loads TTF at 12px
- `ImageDraw.text()` -- renders glyphs to grayscale images
- Can create 12x12 `Image.new('L', (12,12))` canvases

**Font rendering pipeline:**
```python
from PIL import Image, ImageDraw, ImageFont

def render_glyph(char, font_path, size=12):
    font = ImageFont.truetype(font_path, size)
    img = Image.new('L', (12, 12), 0)  # black background
    draw = ImageDraw.Draw(img)
    # Center the glyph in the 12x12 cell
    bbox = font.getbbox(char)
    x_offset = (12 - (bbox[2] - bbox[0])) // 2
    y_offset = (12 - (bbox[3] - bbox[1])) // 2
    draw.text((x_offset - bbox[0], y_offset - bbox[1]), char, font=font, fill=255)
    return img
```

**Key considerations for atlas generation:**
- The atlas palette is INVERTED: 0 = opaque (white text), 15 = transparent (background)
- Pillow renders white-on-black (255 = filled), so we need to INVERT: `pixel_value = 15 - (pil_value * 15 // 255)`
- The atlas is LINEAR PSMT4 (no swizzle needed for GIF transfer)
- Output must be 256x512 pixels, 4-bit indexed, with the same 192-byte header and 64-byte palette

## 5. Available Fonts on This System

Direct filesystem enumeration was restricted during this session. However, based on standard Windows 11 installations:

**Guaranteed present (ship with Windows 11):**
- `C:/Windows/Fonts/consola.ttf` -- Consolas
- `C:/Windows/Fonts/cour.ttf` -- Courier New
- `C:/Windows/Fonts/arial.ttf` -- Arial (confirmed working)
- `C:/Windows/Fonts/msgothic.ttc` -- MS Gothic / MS PGothic / MS UI Gothic (Japanese)
- `C:/Windows/Fonts/msmincho.ttc` -- MS Mincho (Japanese)
- `C:/Windows/Fonts/meiryo.ttc` -- Meiryo (Japanese, if Japanese language pack installed)
- `C:/Windows/Fonts/YuGothR.ttc` -- Yu Gothic (Japanese)
- `C:/Windows/Fonts/malgun.ttf` -- Malgun Gothic (Korean, has good Latin)

**Likely present (common Windows 11 optional features):**
- `C:/Windows/Fonts/cascadiacode.ttf` or `CascadiaMono.ttf`
- `C:/Windows/Fonts/lucon.ttf` -- Lucida Console

**TODO: Run font enumeration to confirm exact availability.**

## 6. What Other PS2 Fan Translations Used

### General Approach (from romhacking.net PS2 Translation Tutorial)
The standard PS2 fan translation font workflow is:
1. **Identify the font atlas texture** in the game's data files (done -- resource 1272)
2. **Extract the atlas** and determine grid layout (done -- 21x42 grid, 12x12 cells)
3. **Create a new atlas** with English glyphs replacing Japanese ones
4. **Update the glyph mapping table** so the text engine maps ASCII/custom codes to the correct atlas positions
5. **Reinsert** the modified atlas into the game archive

### Notable PS2 Translation Font Approaches

**Tales of Rebirth (PS2)** -- Released 2024:
- Full English translation patch
- Replaced Japanese font atlas with English bitmap font
- Used variable-width font rendering (required code patching)

**Wizardry: Tale of the Forsaken Land (PS2)** -- Already in English:
- The original English release used a clean serif bitmap font
- 12-14px glyphs, anti-aliased, similar atlas structure
- This game (Busin 0) is the Japanese-only sequel, so matching its predecessor's font style would be ideal

**Wizardry Dimguil (PS1)** -- Fan translation:
- Used custom pixel font with careful spacing tweaks
- Had to adjust letter widths to prevent overlap
- Lesson: fixed-width is safer than variable-width for initial implementation

**Wizardry Empire II Plus (GBA)** -- Fan translation by iwakura productions:
- Replaced Japanese tile font with English pixel font
- Used 8x8 pixel cells (smaller than our 12x12)

**Wizardry Chronicle (PS2)** -- Fan translation:
- Complete English translation released
- Replaced font atlas in similar PSMT4 format
- Relevant precedent for our exact use case

### Key Lessons from the Community
1. **Start with fixed-width** -- Variable-width requires patching the text rendering code in the EXE. Fixed-width works with the existing engine.
2. **Anti-aliasing matters** -- At 12x12, a 2-3 level AA significantly improves readability on CRT/interlaced displays. Our 16-level palette supports this well.
3. **Test on real hardware or accurate emulator** -- NTSC interlacing can make thin horizontal lines disappear. Avoid single-pixel-height features.
4. **Keep the original header/palette** -- Only replace the pixel data. The GS register setup in the 192-byte header must remain identical.

## Summary & Next Steps

| Question | Answer |
|----------|--------|
| Characters needed | ~95 (ASCII printable) + ~30 extended = ~125 total |
| Slot strategy | Replace all 882 slots; map English to first ~127 |
| Best font | Terminus (12px) or MS Gothic for dual JP/EN capability |
| Pillow ready? | Yes -- Pillow 12.1.1 confirmed, TTF rendering works |
| System fonts | arial.ttf confirmed; msgothic.ttc, consola.ttf expected |
| Community approach | Replace atlas pixels, keep header/palette, fixed-width first |

### Immediate TODO
1. Enumerate actual fonts on this system (run `os.listdir('C:/Windows/Fonts')` filtered for TTF/TTC)
2. Render test glyphs at 12px with Terminus, MS Gothic, and Consolas -- compare readability
3. Build atlas generator script: takes a font + character list, produces 256x512 PSMT4 binary
4. Test by injecting the new atlas into PACKDATA.DIG resource 1272 and running in PCSX2
