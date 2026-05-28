import os, sys, json, time, io
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from pathlib import Path

# Fix Unicode output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

GLYPH_DIR = Path('C:/Programmieren/wizardrytranslation/dumps/glyphs')
OUTPUT_JSON = Path('C:/Programmieren/wizardrytranslation/data/glyph_map_template.json')
FINDINGS_DIR = Path('C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/impl14-template-match')

MAX_GLYPH = 881

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
    glyphs = {}
    for idx in range(MAX_GLYPH + 1):
        gf = GLYPH_DIR / f'glyph_{idx:04d}.png'
        if not gf.exists():
            continue
        img = Image.open(gf).convert('L')
        img = img.resize((12, 12), Image.NEAREST)
        arr = np.array(img)
        binary = (arr < 128).astype(np.uint8)
        glyphs[idx] = binary
    print(f'Loaded {len(glyphs)} glyphs (0-{MAX_GLYPH})')
    return glyphs

def build_char_list():
    chars = []
    chars.append(' ')
    for c in range(0x21, 0x7F):
        chars.append(chr(c))
    for c in range(0xFF01, 0xFF5F):
        chars.append(chr(c))
    for c in range(0x3000, 0x3021):
        chars.append(chr(c))
    for c in range(0x3041, 0x3097):
        chars.append(chr(c))
    for c in range(0x30A1, 0x30FF):
        chars.append(chr(c))
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
    seen = set()
    unique = []
    for c in chars:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique

def render_refs_bitmap(font_path, chars, render_size, canvas_size=12):
    """Render characters using 1-bit mode (no anti-aliasing) for bitmap-like output."""
    refs = {}
    font = ImageFont.truetype(font_path, render_size)

    for char in chars:
        # Render in 1-bit mode to avoid anti-aliasing
        # First render larger, then check
        img = Image.new('1', (canvas_size, canvas_size), 1)  # 1-bit, white background
        draw = ImageDraw.Draw(img)

        bbox = font.getbbox(char)
        if bbox is None:
            continue
        x0, y0, x1, y1 = bbox
        char_w = x1 - x0
        char_h = y1 - y0

        # Center
        offset_x = (canvas_size - char_w) // 2 - x0
        offset_y = (canvas_size - char_h) // 2 - y0

        draw.text((offset_x, offset_y), char, font=font, fill=0)
        arr = np.array(img).astype(np.uint8)
        # In 1-bit: 0=black(ink), 1=white(bg). Invert so ink=1.
        bmp = 1 - arr
        if bmp.sum() > 0:
            refs[char] = bmp

    return refs

def render_refs_grayscale(font_path, chars, render_size, canvas_size=12, threshold=128):
    """Render in grayscale with various thresholds."""
    refs = {}
    font = ImageFont.truetype(font_path, render_size)

    for char in chars:
        img = Image.new('L', (canvas_size, canvas_size), 255)
        draw = ImageDraw.Draw(img)

        bbox = font.getbbox(char)
        if bbox is None:
            continue
        x0, y0, x1, y1 = bbox
        char_w = x1 - x0
        char_h = y1 - y0

        offset_x = (canvas_size - char_w) // 2 - x0
        offset_y = (canvas_size - char_h) // 2 - y0

        draw.text((offset_x, offset_y), char, font=font, fill=0)
        arr = np.array(img)
        bmp = (arr < threshold).astype(np.uint8)
        if bmp.sum() > 0:
            refs[char] = bmp

    return refs

def render_refs_oversize_downscale(font_path, chars, render_size, canvas_size=12):
    """Render at larger size then downscale to 12x12 for better bitmap approximation."""
    refs = {}
    font = ImageFont.truetype(font_path, render_size)
    scale = max(1, render_size // canvas_size)
    big_size = canvas_size * scale

    for char in chars:
        img = Image.new('L', (big_size, big_size), 255)
        draw = ImageDraw.Draw(img)

        bbox = font.getbbox(char)
        if bbox is None:
            continue
        x0, y0, x1, y1 = bbox
        char_w = x1 - x0
        char_h = y1 - y0

        offset_x = (big_size - char_w) // 2 - x0
        offset_y = (big_size - char_h) // 2 - y0

        draw.text((offset_x, offset_y), char, font=font, fill=0)

        # Downscale
        img_small = img.resize((canvas_size, canvas_size), Image.LANCZOS)
        arr = np.array(img_small)
        bmp = (arr < 128).astype(np.uint8)
        if bmp.sum() > 0:
            refs[char] = bmp

    return refs

def match_all_vectorized(glyphs, refs):
    glyph_indices = sorted(glyphs.keys())
    ref_chars = list(refs.keys())
    glyph_matrix = np.array([glyphs[idx].flatten() for idx in glyph_indices], dtype=np.uint8)
    ref_matrix = np.array([refs[c].flatten() for c in ref_chars], dtype=np.uint8)

    results = {}
    batch_size = 100
    for batch_start in range(0, len(glyph_indices), batch_size):
        batch_end = min(batch_start + batch_size, len(glyph_indices))
        batch_glyphs = glyph_matrix[batch_start:batch_end]
        batch_indices = glyph_indices[batch_start:batch_end]

        for i, idx in enumerate(batch_indices):
            if batch_glyphs[i].sum() == 0:
                results[idx] = {'char': ' ', 'score': 1.0, 'blank': True}

        xor_result = np.bitwise_xor(
            batch_glyphs[:, np.newaxis, :],
            ref_matrix[np.newaxis, :, :]
        )
        mismatch_counts = xor_result.sum(axis=2)
        match_scores = 1.0 - mismatch_counts / 144.0

        best_ref_indices = np.argmax(match_scores, axis=1)
        best_scores = np.max(match_scores, axis=1)

        for i, idx in enumerate(batch_indices):
            if idx not in results:
                results[idx] = {
                    'char': ref_chars[best_ref_indices[i]],
                    'score': float(best_scores[i])
                }

    return results

def main():
    t0 = time.time()
    print('=== Template Matching v4 (bitmap mode + multiple strategies) ===')

    font_path = find_font()
    chars = build_char_list()
    print(f'Built character list: {len(chars)} characters')

    glyphs = load_all_glyphs()

    best_config = None
    best_avg = 0
    best_results = None

    # Strategy 1: 1-bit rendering (no anti-aliasing)
    for font_size in [12, 11, 13, 10, 14, 9, 8, 16]:
        t1 = time.time()
        refs = render_refs_bitmap(font_path, chars, font_size, canvas_size=12)
        t2 = time.time()
        if len(refs) < 100:
            print(f'  bitmap size={font_size}: only {len(refs)} refs, skipping')
            continue
        results = match_all_vectorized(glyphs, refs)
        t3 = time.time()
        scores = [r['score'] for r in results.values()]
        avg = np.mean(scores)
        high_conf = sum(1 for s in scores if s >= 0.90)
        config_name = f'bitmap-{font_size}'
        print(f'  {config_name}: {len(refs)} refs in {t2-t1:.1f}s, match {t3-t2:.1f}s, avg={avg:.4f}, >=90%={high_conf}/{len(results)}')
        if avg > best_avg:
            best_avg = avg
            best_config = config_name
            best_results = results

    # Strategy 2: Grayscale with different thresholds
    for font_size in [12, 13, 14]:
        for threshold in [64, 96, 128, 160, 192]:
            t1 = time.time()
            refs = render_refs_grayscale(font_path, chars, font_size, canvas_size=12, threshold=threshold)
            t2 = time.time()
            if len(refs) < 100:
                continue
            results = match_all_vectorized(glyphs, refs)
            t3 = time.time()
            scores = [r['score'] for r in results.values()]
            avg = np.mean(scores)
            high_conf = sum(1 for s in scores if s >= 0.90)
            config_name = f'gray-{font_size}-t{threshold}'
            print(f'  {config_name}: {len(refs)} refs, match {t3-t2:.1f}s, avg={avg:.4f}, >=90%={high_conf}/{len(results)}')
            if avg > best_avg:
                best_avg = avg
                best_config = config_name
                best_results = results

    # Strategy 3: Render at larger size, downscale (simulates bitmap behavior)
    for render_size in [24, 36, 48]:
        t1 = time.time()
        refs = render_refs_oversize_downscale(font_path, chars, render_size, canvas_size=12)
        t2 = time.time()
        if len(refs) < 100:
            continue
        results = match_all_vectorized(glyphs, refs)
        t3 = time.time()
        scores = [r['score'] for r in results.values()]
        avg = np.mean(scores)
        high_conf = sum(1 for s in scores if s >= 0.90)
        config_name = f'oversize-{render_size}'
        print(f'  {config_name}: {len(refs)} refs, match {t3-t2:.1f}s, avg={avg:.4f}, >=90%={high_conf}/{len(results)}')
        if avg > best_avg:
            best_avg = avg
            best_config = config_name
            best_results = results

    # Strategy 4: Try msmincho (Mincho style font, sometimes used in games)
    alt_fonts = [
        'C:/Windows/Fonts/msmincho.ttc',
        'C:/Windows/Fonts/meiryo.ttc',
    ]
    for alt_font in alt_fonts:
        if not os.path.exists(alt_font):
            continue
        font_name = Path(alt_font).stem
        for font_size in [12, 13, 14]:
            t1 = time.time()
            refs = render_refs_bitmap(alt_font, chars, font_size, canvas_size=12)
            t2 = time.time()
            if len(refs) < 100:
                continue
            results = match_all_vectorized(glyphs, refs)
            t3 = time.time()
            scores = [r['score'] for r in results.values()]
            avg = np.mean(scores)
            high_conf = sum(1 for s in scores if s >= 0.90)
            config_name = f'{font_name}-bitmap-{font_size}'
            print(f'  {config_name}: {len(refs)} refs, match {t3-t2:.1f}s, avg={avg:.4f}, >=90%={high_conf}/{len(results)}')
            if avg > best_avg:
                best_avg = avg
                best_config = config_name
                best_results = results

    print(f'\nBest config: {best_config}, avg={best_avg:.4f}')

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
    pct100 = int(np.sum(scores_arr >= 1.0))
    pct95 = int(np.sum(scores_arr >= 0.95))
    pct90 = int(np.sum(scores_arr >= 0.90))
    pct85 = int(np.sum(scores_arr >= 0.85))
    pct80 = int(np.sum(scores_arr >= 0.80))
    low80 = int(np.sum(scores_arr < 0.80))

    print(f'\n=== Final Statistics ===')
    print(f'Total glyphs: {len(output)}')
    print(f'Average match score: {scores_arr.mean():.4f}')
    print(f'Median match score: {np.median(scores_arr):.4f}')
    print(f'Score = 100%: {pct100}')
    print(f'Score >= 95%: {pct95}')
    print(f'Score >= 90%: {pct90}')
    print(f'Score >= 85%: {pct85}')
    print(f'Score >= 80%: {pct80}')
    print(f'Score < 80%: {low80}')

    print('\nSample Mappings (first 30):')
    for idx in range(min(30, len(output))):
        if idx in best_results:
            r = best_results[idx]
            ch = r['char']
            code = f'U+{ord(ch):04X}' if ch else '?'
            print(f'  glyph_{idx:04d} -> {ch} ({code}) (score: {r["score"]:.4f})')

    # Show some from the middle range (likely kana)
    print('\nMappings around index 200-230 (likely kana range):')
    for idx in range(200, min(230, MAX_GLYPH + 1)):
        if idx in best_results:
            r = best_results[idx]
            ch = r['char']
            code = f'U+{ord(ch):04X}' if ch else '?'
            print(f'  glyph_{idx:04d} -> {ch} ({code}) (score: {r["score"]:.4f})')

    print('\nLowest Confidence (bottom 20):')
    sorted_by_score = sorted(best_results.items(), key=lambda x: x[1]['score'])
    for idx, r in sorted_by_score[:20]:
        ch = r['char']
        code = f'U+{ord(ch):04X}' if ch else '?'
        print(f'  glyph_{idx:04d} -> {ch} ({code}) (score: {r["score"]:.4f})')

    print('\nHighest Confidence (top 20, non-blank):')
    non_blank = [(idx, r) for idx, r in best_results.items() if not r.get('blank')]
    sorted_desc = sorted(non_blank, key=lambda x: x[1]['score'], reverse=True)
    for idx, r in sorted_desc[:20]:
        ch = r['char']
        code = f'U+{ord(ch):04X}' if ch else '?'
        print(f'  glyph_{idx:04d} -> {ch} ({code}) (score: {r["score"]:.4f})')

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
    findings_text += f'- Best configuration: {best_config}\n'
    findings_text += f'- Tested multiple rendering strategies: bitmap (1-bit), grayscale with thresholds, oversize-downscale\n'
    findings_text += f'- Tested multiple fonts: msgothic.ttc, msmincho.ttc, meiryo.ttc\n'
    findings_text += f'- Rendered {len(chars)} reference characters covering ASCII, full-width, hiragana, katakana, JIS kanji\n'
    findings_text += f'- Compared each of {len(glyphs)} game glyphs (48x48 downscaled to 12x12 binary) against all references\n'
    findings_text += '- Scoring: pixel-wise match percentage (144 pixels per glyph)\n'
    findings_text += f'- Vectorized numpy matching, total time: {elapsed:.1f}s\n\n'
    findings_text += '## Results\n'
    findings_text += f'- Total glyphs mapped: {len(output)}\n'
    findings_text += f'- Average match score: {scores_arr.mean():.4f}\n'
    findings_text += f'- Median match score: {np.median(scores_arr):.4f}\n'
    findings_text += f'- Perfect match (100%): {pct100}\n'
    findings_text += f'- Near-perfect (>=95%): {pct95}\n'
    findings_text += f'- High confidence (>=90%): {pct90}\n'
    findings_text += f'- Medium confidence (>=85%): {pct85}\n'
    findings_text += f'- Low confidence (<80%): {low80}\n\n'
    findings_text += '## Output Files\n'
    findings_text += '- data/glyph_map_template.json - Simple index to character mapping\n'
    findings_text += '- data/glyph_map_template_detailed.json - Includes confidence scores\n\n'
    findings_text += '## Notes\n'
    findings_text += '- Windows TTF fonts (even MS Gothic) produce different bitmaps than the game font\n'
    findings_text += '- A dedicated Japanese bitmap font (BDF format, like Shinonome 12px) would likely give much better results\n'
    findings_text += '- The Shinonome font server was unreachable during this run\n'
    findings_text += '- Low-confidence matches should be verified manually\n'
    findings_text += '- Consider alternative approaches: OCR with context, or manual verification of common kanji\n'

    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(FINDINGS_DIR / 'FINDINGS.md', 'w', encoding='utf-8') as f:
        f.write(findings_text)
    print(f'\nFindings written to {FINDINGS_DIR / "FINDINGS.md"}')
    print(f'Total elapsed: {elapsed:.1f}s')

if __name__ == '__main__':
    main()
