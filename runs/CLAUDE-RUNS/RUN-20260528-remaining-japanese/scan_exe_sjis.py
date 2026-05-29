"""
Deep scan of SLPM_653.78 EXE for remaining Japanese (SJIS) strings
and potentially player-visible ASCII strings in the data section.
"""
import struct, sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

EXE = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"

# Regions to SKIP
SKIP_RANGES = [
    (0x000000, 0x3B0000),   # Code section
    (0x3EE9D0, 0x3F3500),   # Battle debug / TTY strings
    (0x3DDC00, 0x3DDE00),   # Font data area
]

# Known patched areas (report nearby strings)
PATCHED = {
    0x3FC720: "save slot names",
    0x3F8240: "SJIS string 1",
    0x3F8260: "SJIS string 2",
    0x3C93B0: "NPC names",
}

# Known data tables (label but don't skip - we want to check them)
KNOWN_TABLES = {
    (0x3C3000, 0x3C5300): "Table 2C menu structs",
    (0x3C83C0, 0x3C93A0): "Table 2B chargen grid",
    (0x3C9BF0, 0x3C9DA0): "Table 2A keyboard",
    (0x3C9DA0, 0x3C9DFC): "Table 2E tab labels",
}

def in_skip(offset):
    for s, e in SKIP_RANGES:
        if s <= offset < e:
            return True
    return False

def in_known_table(offset):
    for (s, e), name in KNOWN_TABLES.items():
        if s <= offset < e:
            return name
    return None

def is_sjis_lead(b):
    return (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF)

def is_sjis_trail(b):
    return (0x40 <= b <= 0x7E) or (0x80 <= b <= 0xFC)

def is_halfwidth_kana(b):
    return 0xA1 <= b <= 0xDF

def scan_sjis(data, min_chars=2):
    """Find runs of SJIS double-byte characters."""
    results = []
    i = 0
    n = len(data)
    while i < n - 1:
        if in_skip(i):
            i += 1
            continue
        # Try to build a run of SJIS chars
        if is_sjis_lead(data[i]) and is_sjis_trail(data[i+1]):
            start = i
            chars = 0
            j = i
            while j < n - 1 and is_sjis_lead(data[j]) and is_sjis_trail(data[j+1]):
                chars += 1
                j += 2
            if chars >= min_chars:
                raw = data[start:j]
                try:
                    text = raw.decode('shift_jis', errors='replace')
                except:
                    text = "<decode error>"
                # Filter out likely non-text (all same char, all replacement)
                if text.count('\ufffd') < len(text) // 2:
                    table = in_known_table(start)
                    results.append((start, j - start, chars, text, table))
            i = j
        else:
            i += 1
    return results

def scan_ascii(data, min_len=6):
    """Find runs of printable ASCII in the data section."""
    results = []
    i = 0x3B0000
    n = len(data)
    while i < n:
        if in_skip(i):
            i += 1
            continue
        if 0x20 <= data[i] <= 0x7E:
            start = i
            while i < n and 0x20 <= data[i] <= 0x7E:
                i += 1
            length = i - start
            if length >= min_len:
                text = data[start:start+length].decode('ascii')
                # Skip if it looks like code/debug (common patterns)
                skip_prefixes = ['__', 'sceSif', 'sceGs', 'scePad', 'sceLib',
                                 'sceDma', 'sceVu', 'sceIpu', 'sceCd',
                                 'sce', 'Sce', 'iop_', 'printf', 'fprintf',
                                 'sprintf', 'assert', 'malloc', 'free',
                                 'fopen', 'fclose', 'fread', 'fwrite']
                is_debug = any(text.startswith(p) for p in skip_prefixes)
                if not is_debug:
                    table = in_known_table(start)
                    results.append((start, length, text, table))
        else:
            i += 1
    return results

def nearby_patched(offset, radius=256):
    """Check if offset is near a known patched area."""
    for addr, name in PATCHED.items():
        if abs(offset - addr) < radius:
            return f"near {name} (0x{addr:06X})"
    return None

def main():
    with open(EXE, "rb") as f:
        data = f.read()

    print(f"EXE size: {len(data)} bytes (0x{len(data):06X})")
    print(f"Scanning data section 0x3B0000 - 0x{len(data):06X}...")
    print()

    # === SJIS SCAN ===
    print("=" * 80)
    print("SHIFT-JIS STRING SCAN (2+ double-byte chars)")
    print("=" * 80)
    sjis_results = scan_sjis(data, min_chars=2)

    # Group by region
    for offset, nbytes, nchars, text, table in sjis_results:
        if offset < 0x3B0000:
            continue
        near = nearby_patched(offset)
        loc = f"0x{offset:06X}"
        extra = ""
        if table:
            extra += f" [{table}]"
        if near:
            extra += f" [{near}]"
        # Mark if it contains actual Japanese (not just symbols)
        has_jp = any(ord(c) > 0x3000 for c in text)
        tag = "JP" if has_jp else "SYM"
        print(f"  {loc}  {nbytes:4d}B  {nchars:3d}ch  [{tag}] {extra}  {text!r}")

    print()
    print(f"Total SJIS runs found in data section: {sum(1 for o,_,_,_,_ in sjis_results if o >= 0x3B0000)}")

    # === ASCII SCAN (interesting only) ===
    print()
    print("=" * 80)
    print("ASCII STRING SCAN (6+ chars, data section, filtered)")
    print("=" * 80)
    ascii_results = scan_ascii(data, min_len=6)

    # Filter to potentially interesting strings
    interesting_ascii = []
    # Japanese romanization patterns, menu-like words, game terms
    game_keywords = ['menu', 'item', 'spell', 'magic', 'attack', 'defend',
                     'equip', 'status', 'save', 'load', 'party', 'name',
                     'level', 'class', 'race', 'align', 'hp', 'mp',
                     'str', 'int', 'vit', 'agi', 'luk', 'piety',
                     'gold', 'shop', 'inn', 'guild', 'temple',
                     'battle', 'dungeon', 'floor', 'quest',
                     'yes', 'no', 'ok', 'cancel', 'confirm',
                     'new', 'game', 'continue', 'option', 'system',
                     'weapon', 'armor', 'shield', 'helmet', 'boot',
                     'ring', 'amulet', 'potion', 'scroll',
                     'warrior', 'mage', 'priest', 'thief', 'bishop',
                     'samurai', 'lord', 'ninja', 'monk', 'valkyrie',
                     'human', 'elf', 'dwarf', 'gnome', 'hobbit',
                     'good', 'evil', 'neutral']

    for offset, length, text, table in ascii_results:
        near = nearby_patched(offset)
        # Show all strings near patched areas, in known tables, or matching keywords
        is_interesting = (near or table or
                         any(kw in text.lower() for kw in game_keywords) or
                         length >= 20)  # long strings are interesting
        if is_interesting:
            loc = f"0x{offset:06X}"
            extra = ""
            if table:
                extra += f" [{table}]"
            if near:
                extra += f" [{near}]"
            interesting_ascii.append((offset, length, text, extra))
            print(f"  {loc}  {length:4d}ch {extra}  {text!r}")

    print()
    print(f"Total interesting ASCII strings: {len(interesting_ascii)}")
    print(f"Total ASCII strings (all): {len(ascii_results)}")

    # === NEIGHBORHOOD SCAN around patched areas ===
    print()
    print("=" * 80)
    print("NEIGHBORHOOD SCAN (256 bytes around each patched area)")
    print("=" * 80)
    for addr, name in sorted(PATCHED.items()):
        start = max(0, addr - 256)
        end = min(len(data), addr + 256)
        print(f"\n--- Around 0x{addr:06X} ({name}) ---")
        # Show hex + ascii dump of nearby area
        for row_start in range(start, end, 16):
            row = data[row_start:row_start+16]
            hexpart = ' '.join(f'{b:02X}' for b in row)
            ascpart = ''.join(chr(b) if 0x20 <= b <= 0x7E else '.' for b in row)
            # Check if this row has SJIS
            has_sjis = False
            for k in range(0, len(row)-1):
                if is_sjis_lead(row[k]) and is_sjis_trail(row[k+1]):
                    has_sjis = True
                    break
            marker = " *SJIS*" if has_sjis else ""
            print(f"  0x{row_start:06X}: {hexpart:<48s}  {ascpart}{marker}")

    # === SPECIFIC AREA SCANS ===
    print()
    print("=" * 80)
    print("SCAN OF UNEXPLORED DATA RANGES")
    print("=" * 80)

    # Areas between known tables that might have strings
    unexplored = [
        (0x3B0000, 0x3C3000, "Pre-table area"),
        (0x3C5300, 0x3C83C0, "Between Table2C and Table2B"),
        (0x3C93A0, 0x3C9BF0, "Between Table2B and Table2A (includes NPC names)"),
        (0x3C9DFC, 0x3DDC00, "Between Table2E and font data"),
        (0x3DDE00, 0x3EE9D0, "Between font data and debug strings"),
        (0x3F3500, 0x3FC720, "Between debug strings and save names"),
        (0x3FC800, 0x3FD000, "After save names to end of data"),
        (0x3FD000, len(data), "Post-data section"),
    ]

    for start, end, label in unexplored:
        if start >= len(data):
            continue
        end = min(end, len(data))
        sjis_count = 0
        for offset, nbytes, nchars, text, table in sjis_results:
            if start <= offset < end:
                sjis_count += 1
        ascii_count = sum(1 for o, l, t, tb in ascii_results if start <= o < end)
        print(f"\n  {label} (0x{start:06X} - 0x{end:06X}, {end-start} bytes)")
        print(f"    SJIS runs: {sjis_count}, ASCII strings: {ascii_count}")
        # Show SJIS hits in this range
        for offset, nbytes, nchars, text, table in sjis_results:
            if start <= offset < end:
                has_jp = any(ord(c) > 0x3000 for c in text)
                tag = "JP" if has_jp else "SYM"
                print(f"      0x{offset:06X}  {nchars}ch [{tag}]  {text!r}")

    return sjis_results, ascii_results, interesting_ascii

if __name__ == "__main__":
    sjis_results, ascii_results, interesting_ascii = main()
