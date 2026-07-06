"""Compute spell-desc glyph lengths, classify FITS/OVERFLOW vs the box width,
and wrap overflowers at word boundaries inserting ' / ' line breaks.

Box model (evidence):
  - block2 is a cell grid; offset table indexes by cell. Names+descriptions use
    the SAME full-width cell pitch (romanized names occupy full-width katakana cells).
  - => our lowercase ASCII glyphs are 1 full-width cell each (monospaced).
  - MULTI-LINE: pristine g53 has TWO 0xFFFE breaks ([17,20,0] segments). Box height
    grows from the trailing/embedded 0xFFFE count (EXE 0x38DA80 -> jal 0x3A3A10).
  - Per-line width budget = the pristine line budget. Widest pristine single line = 27
    cells (g35,g50). Standard line = 15. We use a SAFE per-line cap = 24 cells
    (under the 26-27 hardware max, leaving margin), matching pristine wrap (g53 17/20).
"""
import json, re

JSON_PATH = 'C:/programmieren/wizardrytranslation/data/r39_spell_descriptions.json'
LINE_CAP = 26      # max glyph cells per rendered line (= widest pristine JP line; <=27 hw max)

# Same normalization the encoder does (lowercase, drop .,'-()" , map ; -> break)
DROP = set(".,'-()\"")
ALLOWED = set('abcdefghijklmnopqrstuvwxyz0123456789/:?!~% ')

def normalize(text):
    """Return the text as the encoder will see it (per line, after drops)."""
    text = text.lower().replace(';', ' / ')
    return text

def glyph_len_line(s):
    """Count glyph cells in a single line segment (after dropping DROP chars).
    spaces ARE cells (id 0). slash inside is a cell too if literal, but we only
    use ' / ' as a break which is NOT a cell. Within a line there is no ' / '."""
    n = 0
    for ch in s:
        if ch in DROP:
            continue
        n += 1
    return n

def segments(text):
    """Split normalized text into rendered line segments at ' / '."""
    return normalize(text).split(' / ')

def total_glyph_len(text):
    """Sum of cells across all segments (excludes the break markers themselves)."""
    return sum(glyph_len_line(seg.strip()) for seg in segments(text))

def wrap_text(text, cap=LINE_CAP):
    """Greedy word-wrap the (already drop-normalized, lowercased) text into lines
    of <= cap glyph cells, joining with ' / '. Preserves any existing ' / ' breaks
    as hard breaks, then re-wraps each piece."""
    # Work on the encoder-normalized form so our cell counts match the encoder.
    hard_parts = segments(text)
    out_lines = []
    for part in hard_parts:
        part = part.strip()
        if not part:
            continue
        words = part.split()
        line = ''
        for w in words:
            # cells of w after drops
            wl = glyph_len_line(w)
            if line == '':
                line = w
            elif glyph_len_line(line) + 1 + wl <= cap:   # +1 for the space cell
                line = line + ' ' + w
            else:
                out_lines.append(line)
                line = w
        if line:
            out_lines.append(line)
    return ' / '.join(out_lines)

# Hand-authored wraps for the two entries that would otherwise need 3 lines
# (greedy wrap leaves an orphan word). These keep each rendered line <= cap and
# stay within 2 lines, mirroring pristine g53's 2-line max.
MANUAL = {
    # "Raises an ally's hit and attack; can strike immune foes"
    '31': "raises ally hit and attack / can strike immune foes",
    # "Fully restores stamina; blocks ailments while moving"
    '41': "fully restores stamina / no ailments while moving",
}

def main():
    spec = json.load(open(JSON_PATH, encoding='utf-8'))
    descs = spec['descriptions']
    pristine_jp = set(str(x) for x in spec.get('_pristine_jp_records', []))

    overflow = []
    new_descs = {}
    for g, en in descs.items():
        if g in pristine_jp:
            new_descs[g] = en
            continue
        segs = segments(en)
        maxline = max(glyph_len_line(s.strip()) for s in segs)
        tot = total_glyph_len(en)
        fits = maxline <= LINE_CAP
        if g in MANUAL:
            wrapped = MANUAL[g]
            new_descs[g] = wrapped
            wseg = segments(wrapped)
            wmax = max(glyph_len_line(s.strip()) for s in wseg)
            overflow.append((int(g), maxline, tot, len([s for s in wseg if s.strip()]), wmax, en, wrapped))
        elif fits:
            new_descs[g] = en
        else:
            wrapped = wrap_text(en)
            new_descs[g] = wrapped
            wseg = segments(wrapped)
            wmax = max(glyph_len_line(s.strip()) for s in wseg)
            overflow.append((int(g), maxline, tot, len([s for s in wseg if s.strip()]), wmax, en, wrapped))

    overflow.sort()
    print(f"LINE_CAP = {LINE_CAP} glyph cells/line (full-width)")
    print(f"total non-pristine descriptions: {sum(1 for g in descs if g not in pristine_jp)}")
    print(f"OVERFLOWED (maxline > {LINE_CAP}): {len(overflow)}")
    print()
    print("g  | oldmax tot | lines newmax | text")
    for g, ml, tot, nl, wm, en, wr in overflow:
        print(f"g{g:<3} oldmax={ml:2d} tot={tot:3d} -> {nl} lines newmax={wm:2d}")
        print(f"      BEFORE: {en}")
        print(f"      AFTER : {wr}")
    # write corrected json
    spec['descriptions'] = new_descs
    out = json.dumps(spec, indent=1, ensure_ascii=False)
    open(JSON_PATH, 'w', encoding='utf-8').write(out)
    print()
    print(f"WROTE corrected {JSON_PATH}")

if __name__ == '__main__':
    main()
