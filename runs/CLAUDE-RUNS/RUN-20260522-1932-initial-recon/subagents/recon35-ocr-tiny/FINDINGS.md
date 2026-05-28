# OCR for Tiny (12x12) Japanese Pixel Characters -- Research Findings

**Date:** 2026-05-22
**Problem:** Standard OCR engines (EasyOCR, RapidOCR) return NO RESULT on 12x12 pixel Japanese glyphs extracted from a PS2 game font atlas, even when upscaled 8x to 96x96.

---

## Executive Summary

Standard OCR is the **wrong approach** for this problem. The glyphs are machine-rendered bitmap font tiles, not handwritten or printed text. The correct approach is **direct bitmap template matching** against a known Japanese bitmap font database. This sidesteps OCR entirely and should give near-perfect accuracy.

---

## Why Standard OCR Fails

1. **Too few pixels.** Tesseract needs ~300 DPI; a 12px glyph at screen resolution is ~72 DPI. Upscaling adds no information -- just blurry edges.
2. **No text layout context.** OCR engines expect words/lines of text with whitespace and baselines. Isolated single-glyph crops confuse page segmentation.
3. **Training data mismatch.** EasyOCR/Tesseract are trained on printed/handwritten text, not pixelated bitmap font renderings.
4. **Japanese complexity.** Even working OCR needs special handling for CJK -- thousands of character classes vs. ~100 for Latin.

---

## Recommended Approaches (Ranked by Feasibility)

### 1. DIRECT BITMAP TEMPLATE MATCHING (Best Approach)

**Concept:** The PS2 game uses a specific bitmap font. If we can identify or reconstruct that font, we compare each extracted 12x12 glyph pixel-for-pixel against every glyph in the reference font and pick the closest match.

**Why this works:** Machine-rendered bitmap fonts are deterministic. The same character always produces the exact same pixel pattern. This means a simple pixel comparison (XOR, hamming distance, or normalized cross-correlation) will give a perfect or near-perfect match.

**Implementation plan:**

```python
import numpy as np
from bdfparser import Font  # pip install bdfparser

# 1. Load a reference Japanese BDF bitmap font (12px)
font = Font("japanese-12px.bdf")

# 2. For each glyph in the font, render to a numpy array
reference_db = {}
for codepoint in font.iterglyphs():
    glyph = font.glyph(codepoint)
    bitmap = glyph.draw().todata(2)  # binary bitmap
    arr = np.array(bitmap, dtype=np.uint8)
    reference_db[codepoint] = arr

# 3. For each extracted 12x12 tile from the game:
def identify_glyph(tile_array, reference_db):
    best_match = None
    best_score = float('inf')
    for codepoint, ref in reference_db.items():
        # Resize ref to match tile if needed
        # XOR distance: count differing pixels
        dist = np.sum(tile_array != ref)
        if dist < best_score:
            best_score = dist
            best_match = codepoint
    return best_match, best_score
```

**Reference font sources (12px Japanese BDF fonts):**
- **Japanese Bitmap Font Collection:** <http://openlab.ring.gr.jp/efont/japanese/index.html.en>
  - Contains 10, 12, 14, 16, 20 pixel Japanese fonts (JIS X 0208, JIS X 0201, JIS X 0213) in BDF format
  - The 12-pixel fonts (e.g., `shnmk12`) are the exact size match
- **Fedora japanese-bitmap-fonts package:** Includes `shnmk12` for JISX0208.1983-0
- **Jiskan fonts:** Public domain Japanese bitmap fonts in various sizes

**Python libraries for BDF parsing:**
- `bdfparser` (pip install bdfparser) -- parses BDF fonts, renders glyphs, outputs to numpy/PIL
  - GitHub: <https://github.com/tomchen/bdfparser>
  - Docs: <https://font.tomchen.org/bdfparser_py/>
- `bdffont` (pip install bdffont) -- alternative BDF manipulation library

**Key advantage:** No ML model needed. No training. Works immediately. Deterministic results.

---

### 2. MULTI-FONT TEMPLATE MATCHING (If exact font is unknown)

If the game's font doesn't exactly match any available BDF font, try multiple reference fonts and use fuzzy matching:

```python
from skimage.metrics import structural_similarity as ssim
import cv2

def fuzzy_match(tile, reference_db, threshold=0.85):
    best_match = None
    best_score = -1
    for codepoint, ref in reference_db.items():
        # Resize both to same dimensions if needed
        ref_resized = cv2.resize(ref, (tile.shape[1], tile.shape[0]),
                                  interpolation=cv2.INTER_NEAREST)
        score = ssim(tile, ref_resized)
        if score > best_score:
            best_score = score
            best_match = codepoint
    return best_match, best_score
```

**Matching metrics to try (in order of effectiveness for bitmap fonts):**
1. **XOR + Hamming distance** -- fastest, works perfectly for exact font matches
2. **Normalized cross-correlation** (cv2.matchTemplate with TM_CCORR_NORMED)
3. **SSIM** (structural similarity) -- tolerates slight rendering differences
4. **Perceptual hashing (pHash)** -- 64-bit hash per glyph, very fast lookup
   - Library: `imagehash` (pip install imagehash)
   - Reduces each glyph to a 64-bit fingerprint using DCT
   - Compare via Hamming distance between hashes

---

### 3. BUILD YOUR OWN REFERENCE FROM THE FONT ATLAS

Since you already have the font atlas image from the game, you can build the reference database directly:

1. **Grid-slice the font atlas** into individual 12x12 tiles
2. **Determine the encoding order** (typically JIS X 0208 row-major, or Shift-JIS sequential)
3. **Map tile index to character code** using the game's character table
4. This effectively creates a perfect lookup table -- no OCR needed at all

**ROM hacking approach:**
- Games store fonts as tile grids where position = character code
- Character table files (.tbl) map hex values to characters
- Tools like TaBuLar can generate Japanese character tables
- The Wizardry community has active translation projects: <https://wizardry.wiki.gg/wiki/Fan_translation>

**PS2 Translation Tutorial:** <https://www.romhacking.net/documents/919/>

---

### 4. NEURAL NETWORK APPROACHES (If template matching fails)

If the font is anti-aliased, has variable widths, or doesn't match any reference:

**Kuzushiji-MNIST / KMNIST:**
- GitHub: <https://github.com/rois-codh/kmnist>
- Datasets: KMNIST (10 classes, 28x28), Kuzushiji-49 (49 classes, 28x28), Kuzushiji-Kanji (3,832 classes, 64x64)
- Problem: Trained on handwritten cursive characters, not pixel fonts
- Could work if fine-tuned on pixel font data

**ETL Character Database:**
- URL: <https://etlcdb.db.aist.go.jp/?lang=en>
- ~1.2 million character images: handwritten + printed hiragana, katakana, educational kanji, JIS level 1 kanji
- Contains printed character samples that may be closer to bitmap fonts
- Datasets ETL-1 through ETL-9 with different formats

**DaKanji Single Kanji Recognition:**
- GitHub: <https://github.com/CaptainDario/DaKanji-Single-Kanji-Recognition>
- CNN (EfficientNet) trained on ETL + KanjiVG data
- Accepts grayscale images of any size
- Might work on 12x12 if upscaled, but untested on pixel fonts

**Custom CNN approach:**
- Train a small CNN on rendered glyphs from multiple Japanese bitmap fonts
- Input: 12x12 or upscaled 28x28 grayscale
- Output: Unicode codepoint classification
- Would need to render training data from BDF fonts with slight augmentation (shift by 1px, etc.)

---

### 5. TESSERACT WITH SPECIFIC CONFIGURATION (Low probability of success)

If you still want to try OCR, these settings might help:

```bash
# Upscale first
convert input.png -resize 400% -type Grayscale upscaled.png

# Run tesseract with:
tesseract upscaled.png output \
  -l jpn \
  --psm 10 \          # Single character mode
  --oem 1 \           # LSTM engine
  -c textord_old_xheight=1 \
  -c textord_min_xheight=35 \
  -c textord_max_noise_size=18
```

- **PSM 10** = "Treat the image as a single character" -- critical for isolated glyphs
- **PSM 13** = "Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific"
- Add white border padding (at least 10px) around the glyph before processing
- Upscale with nearest-neighbor interpolation (not bilinear) to preserve pixel edges

**Verdict:** Even with these settings, Tesseract on pixel fonts is unreliable. Use template matching instead.

---

## Implementation Roadmap

### Phase 1: Quick Win -- Font Atlas Self-Mapping
1. Slice the game's font atlas into a grid of 12x12 tiles
2. Determine the character encoding order (inspect the game binary for the character table)
3. Assign each tile position a Unicode codepoint
4. Result: a complete glyph-to-character mapping with zero OCR

### Phase 2: If Encoding is Unknown -- Template Match Against BDF Fonts
1. Download Japanese 12px BDF fonts from openlab.ring.gr.jp/efont
2. Parse with `bdfparser`, render all glyphs to numpy arrays
3. Compare each atlas tile against all reference glyphs using XOR/hamming distance
4. Pick the best match for each tile
5. Manual verification of any ambiguous matches (distance > 0)

### Phase 3: Fallback -- Perceptual Hash Index
1. Compute pHash for every reference glyph (from multiple font sources)
2. Build a hash-to-codepoint lookup dictionary
3. For each atlas tile, compute pHash and find nearest match
4. Much faster than pixel-by-pixel for large character sets (3000+ kanji)

---

## Key Tools and Libraries

| Tool | Purpose | Install |
|------|---------|---------|
| `bdfparser` | Parse BDF bitmap fonts, render glyphs | `pip install bdfparser` |
| `bdffont` | Alternative BDF font library | `pip install bdffont` |
| `imagehash` | Perceptual hashing (pHash, dHash, aHash) | `pip install imagehash` |
| `opencv-python` | Template matching, image processing | `pip install opencv-python` |
| `scikit-image` | SSIM comparison | `pip install scikit-image` |
| `tensorfont` | Convert font glyphs to numpy arrays | `pip install tensorfont` |
| `Pillow` | Image manipulation | `pip install Pillow` |
| `numpy` | Array operations for pixel comparison | `pip install numpy` |

---

## Reference Font Sources

| Source | Sizes | Coverage | Format | URL |
|--------|-------|----------|--------|-----|
| efont Japanese collection | 10,12,14,16,20px | JIS X 0208/0201/0213 | BDF | <http://openlab.ring.gr.jp/efont/japanese/index.html.en> |
| shnmk12 (Fedora) | 12px | JIS X 0208 | BDF | Fedora `japanese-bitmap-fonts` package |
| Jiskan16 | 16px | JIS X 0213 | BDF | Public domain |
| ETL Character DB | Various | Full JIS | Raw images | <https://etlcdb.db.aist.go.jp/> |

---

## Sources

- [Tesseract Small Font Issue #161](https://github.com/tesseract-ocr/tesseract/issues/161)
- [Tesseract Improve Quality Docs](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html)
- [DaKanji Single Kanji Recognition](https://github.com/CaptainDario/DaKanji-Single-Kanji-Recognition)
- [Kuzushiji-MNIST (KMNIST)](https://github.com/rois-codh/kmnist)
- [ETL Character Database](https://etlcdb.db.aist.go.jp/?lang=en)
- [BDFParser Python Library](https://github.com/tomchen/bdfparser)
- [Japanese Bitmap Font Collection](http://openlab.ring.gr.jp/efont/japanese/index.html.en)
- [OpenCV Template Matching Tutorial](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html)
- [imagehash - Perceptual Hashing](https://github.com/JohannesBuchner/imagehash)
- [Tensorfont - Glyphs to NumPy](https://simoncozens.github.io/tensorfont/)
- [PS2 Translation Tutorial](https://www.romhacking.net/documents/919/)
- [Wizardry Fan Translation Wiki](https://wizardry.wiki.gg/wiki/Fan_translation)
- [PyImageSearch - Template Matching](https://pyimagesearch.com/2021/03/22/opencv-template-matching-cv2-matchtemplate/)
- [PyImageSearch - Compare Two Images](https://pyimagesearch.com/2014/09/15/python-compare-two-images/)
- [Libretro OCR](https://www.libretro.com/index.php/category/ocr/)
- [SSIM in Python](https://medium.com/@danielyogatama.dy/ssim-on-python-eb1a76a2799b)
- [ROM Hacking Getting Started](https://www.romhacking.net/start/)
