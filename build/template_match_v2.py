import os, sys, json, time
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from pathlib import Path

GLYPH_DIR = Path('C:/Programmieren/wizardrytranslation/dumps/glyphs')
OUTPUT_JSON = Path('C:/Programmieren/wizardrytranslation/data/glyph_map_template.json')
FINDINGS_DIR = Path('C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/impl14-template-match')

def find_font():
    candidates = [
        'C:/Windows/Fonts/msgothic.ttc',
        'C:/Windows/Fonts/meiryo.ttc',
        'C:/Windows/Fonts/msmincho.ttc',
        'C:/Windows/Fonts/YuGothM.ttc',
    ]
    for path in candidates:
        if os.path.exists(path):
            print(f'Found font: {path}')
            return path
    print('ERROR: No Japanese font found!')
    sys.exit(1)

def load_all_glyphs():
    glyph_files = sorted(GLYPH_DIR.glob('glyph_*.png'))
    print(f'Found {len(glyph_files)} glyph files')
    glyphs = {}
    for gf in glyph_files:
        idx = int(gf.stem.split('_')[1])
        img = Image.open(gf).convert('L')
        img = img.resize((12, 12), Image.NEAREST)
        arr = np.array(img)
        binary = (arr < 128).astype(np.uint8)
        glyphs[idx] = binary
    return glyphs

def build_char_list():
    chars = []
    chars.append(' ')
    # ASCII printable
    for c in range(0x21, 0x7F):
        chars.append(chr(c))
    # Full-width ASCII
    for c in range(0xFF01, 0xFF5F):
        chars.append(chr(c))
    # Japanese punctuation
    for c in range(0x3000, 0x3021):
        chars.append(chr(c))
    # Hiragana
    for c in range(0x3041, 0x3097):
        chars.append(chr(c))
    # Katakana
    for c in range(0x30A1, 0x30FF):
        chars.append(chr(c))
    # All Shift-JIS double-byte characters
    for high in range(0x81, 0xA0):
        for low in range(0x40, 0xFD):
            if low == 0x7F:
                continue
            try:
                c = bytes([high, low]).decode('shift_jis')
                chars.append(c)
            except (UnicodeDecodeError, ValueError):
                continue
    for high in range(0xE0, 0xF0):
        for low in range(0x40, 0xFD):
            if low == 0x7F:
                continue
            try:
                c = bytes([high, low]).decode('shift_jis')
                chars.append(c)
            except (UnicodeDecodeError, ValueError):
                continue
    # Deduplicate
    seen = set()
    unique = []
    for c in chars:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique

def render_refs(font, chars, size=12, mode='centered'):
    refs = {}
    for char in chars:
        img = Image.new('L', (size, size), 255)
        draw = ImageDraw.Draw(img)
        if mode == 'centered':
            bbox = font.getbbox(char)
            if bbox is None:
                continue
            x0, y0, x1, y1 = bbox
            char_w = x1 - x0
            char_h = y1 - y0
            offset_x = (size - char_w) // 2 - x0
            offset_y = (size - char_h) // 2 - y0
            draw.text((offset_x, offset_y), char, font=font, fill=0)
        else:
            draw.text((0, 0), char, font=font, fill=0)
        arr = np.array(img)
        bmp = (arr < 128).astype(np.uint8)
        if bmp.sum() > 0:
            refs[char] = bmp
    return refs

def match_all_vectorized(glyphs, refs):
    # Build matrices for vectorized matching
    glyph_indices = sorted(glyphs.keys())
    ref_chars = list(refs.keys())

    # Stack all glyph bitmaps into a matrix: (N_glyphs, 144)
    glyph_matrix = np.array([glyphs[idx].flatten() for idx in glyph_indices], dtype=np.uint8)
    # Stack all ref bitmaps: (N_refs, 144)
    ref_matrix = np.array([refs[c].flatten() for c in ref_chars], dtype=np.uint8)

    results = {}

    # Process in batches to avoid memory issues
    batch_size = 100
    for batch_start in range(0, len(glyph_indices), batch_size):
        batch_end = min(batch_start + batch_size, len(glyph_indices))
        batch_glyphs = glyph_matrix[batch_start:batch_end]  # (batch, 144)
        batch_indices = glyph_indices[batch_start:batch_end]

        # For blank glyphs, handle separately
        for i, idx in enumerate(batch_indices):
            if batch_glyphs[i].sum() == 0:
                results[idx] = {'char': ' ', 'score': 1.0, 'blank': True}

        # Compute match scores: for each glyph in batch, compare with all refs
        # XOR gives mismatches, so matching = 144 - sum(XOR)
        # (batch, 1, 144) XOR (1, N_refs, 144) -> (batch, N_refs, 144)
        # Then sum along axis 2 gives mismatch count
        xor_result = np.bitwise_xor(
            batch_glyphs[:, np.newaxis, :],  # (batch, 1, 144)
            ref_matrix[np.newaxis, :, :]      # (1, N_refs, 144)
        )
        mismatch_counts = xor_result.sum(axis=2)  # (batch, N_refs)
        match_scores = 1.0 - mismatch_counts / 144.0  # (batch, N_refs)

        best_ref_indices = np.argmax(match_scores, axis=1)
        best_scores = np.max(match_scores, axis=1)

        for i, idx in enumerate(batch_indices):
            if idx not in results:  # Skip already-handled blanks
                results[idx] = {
                    'char': ref_chars[best_ref_indices[i]],
                    'score': float(best_scores[i])
                }

    return results

def main():
    t0 = time.time()
    print('=== Template Matching for Glyph Identification (v2 - vectorized) ===')

    font_path = find_font()
    chars = build_char_list()
    print(f'Built character list: {len(chars)} characters')

    glyphs = load_all_glyphs()
    print(f'Loaded {len(glyphs)} glyphs')

    # Try a focused set of font sizes and rendering modes
    configs = [
        (12, 'centered'), (12, 'topleft'),
        (10, 'centered'), (10, 'topleft'),
        (11, 'centered'), (11, 'topleft'),
        (13, 'centered'), (13, 'topleft'),
        (14, 'centered'), (9, 'centered'),
        (8, 'centered'), (16, 'centered'),
    ]

    best_config = None
    best_avg = 0
    best_results = None

    for font_size, mode in configs:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f'  Cannot load font at size {font_size}: {e}')
            continue

        t1 = time.time()
        refs = render_refs(font, chars, size=12, mode=mode)
        t2 = time.time()
        print(f'  size={font_size}, mode={mode}: rendered {len(refs)} refs in {t2-t1:.1f}s', end='')

        results = match_all_vectorized(glyphs, refs)
        t3 = time.time()

        scores = [r['score'] for r in results.values()]
        avg = np.mean(scores)
        high_conf = sum(1 for s in scores if s >= 0.90)
        print(f', matched in {t3-t2:.1f}s, avg={avg:.4f}, >=90%={high_conf}/{len(results)}')

        if avg > best_avg:
            best_avg = avg
            best_config = (font_size, mode)
            best_results = results

    font_size, mode = best_config
    print(f'\nBest config: size={font_size}, mode={mode}, avg={best_avg:.4f}')

    # Save results
    output = {}
    scores_list = []
    for idx, res in sorted(best_results.items()):
        output[str(idx)] = res['char']
        scores_list.append(res['score'])

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'Saved mapping to {OUTPUT_JSON}')

    scores_arr = np.array(scores_list)
    pct95 = int(np.sum(scores_arr >= 0.95))
    pct90 = int(np.sum(scores_arr >= 0.90))
    pct85 = int(np.sum(scores_arr >= 0.85))
    pct80 = int(np.sum(scores_arr >= 0.80))
    low80 = int(np.sum(scores_arr < 0.80))

    print(f'\n=== Final Statistics ===')
    print(f'Total glyphs: {len(output)}')
    print(f'Average match score: {scores_arr.mean():.4f}')
    print(f'Median match score: {np.median(scores_arr):.4f}')
    print(f'Score >= 95%: {pct95}')
    print(f'Score >= 90%: {pct90}')
    print(f'Score >= 85%: {pct85}')
    print(f'Score >= 80%: {pct80}')
    print(f'Score < 80%: {low80}')

    print('\nSample Mappings (first 30):')
    for idx in range(min(30, len(output))):
        if idx in best_results:
            r = best_results[idx]
            print(f'  glyph_{idx:04d} -> {repr(r["char"])} (score: {r["score"]:.4f})')

    print('\nLowest Confidence Matches (bottom 20):')
    sorted_by_score = sorted(best_results.items(), key=lambda x: x[1]['score'])
    for idx, r in sorted_by_score[:20]:
        print(f'  glyph_{idx:04d} -> {repr(r["char"])} (score: {r["score"]:.4f})')

    print('\nHighest Confidence Matches (top 20):')
    sorted_by_score_desc = sorted(best_results.items(), key=lambda x: x[1]['score'], reverse=True)
    for idx, r in sorted_by_score_desc[:20]:
        print(f'  glyph_{idx:04d} -> {repr(r["char"])} (score: {r["score"]:.4f})')

    # Save detailed results
    detailed = {}
    for idx, res in sorted(best_results.items()):
        detailed[str(idx)] = {'char': res['char'], 'score': round(res['score'], 4)}
    detailed_path = OUTPUT_JSON.parent / 'glyph_map_template_detailed.json'
    with open(detailed_path, 'w', encoding='utf-8') as f:
        json.dump(detailed, f, ensure_ascii=False, indent=2)
    print(f'Saved detailed results to {detailed_path}')

    # Write findings
    elapsed = time.time() - t0
    findings_text = '# Template Matching Findings\n\n'
    findings_text += '## Method\n'
    findings_text += f'- Used TTF font: {font_path} at size {font_size}px, rendering: {mode}\n'
    findings_text += f'- Rendered {len(chars)} reference characters covering ASCII, full-width, hiragana, katakana, JIS kanji\n'
    findings_text += '- Compared each of 882 game glyphs (48x48 downscaled to 12x12 binary) against all references\n'
    findings_text += '- Scoring: pixel-wise match percentage (144 pixels per glyph)\n'
    findings_text += f'- Vectorized numpy matching, total time: {elapsed:.1f}s\n\n'
    findings_text += '## Results\n'
    findings_text += f'- Total glyphs mapped: {len(output)}\n'
    findings_text += f'- Average match score: {scores_arr.mean():.4f}\n'
    findings_text += f'- Median match score: {np.median(scores_arr):.4f}\n'
    findings_text += f'- Perfect/near-perfect (>=95%): {pct95}\n'
    findings_text += f'- High confidence (>=90%): {pct90}\n'
    findings_text += f'- Medium confidence (>=85%): {pct85}\n'
    findings_text += f'- Low confidence (<80%): {low80}\n\n'
    findings_text += '## Output Files\n'
    findings_text += '- data/glyph_map_template.json - Simple index to character mapping\n'
    findings_text += '- data/glyph_map_template_detailed.json - Includes confidence scores\n\n'
    findings_text += '## Notes\n'
    findings_text += '- TTF fonts anti-alias even at small sizes, so exact pixel match is unlikely\n'
    findings_text += '- The game likely used a bitmap font (possibly Shinonome or similar)\n'
    findings_text += '- Low-confidence matches should be verified manually\n'

    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(FINDINGS_DIR / 'FINDINGS.md', 'w', encoding='utf-8') as f:
        f.write(findings_text)
    print(f'\nFindings written to {FINDINGS_DIR / "FINDINGS.md"}')
    print(f'Total elapsed: {elapsed:.1f}s')

if __name__ == '__main__':
    main()
