import sys, io, struct, json, zipfile, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
LOG = open("dumps/batch_xref_log.txt", "w", encoding="utf-8")
def log(msg):
    LOG.write(msg + "\n"); LOG.flush(); print(msg)

# Load existing mapping
mapping = {int(k): v for k, v in json.load(open("data/msg_glyph_map.json", encoding="utf-8")).items()}
log(f"Starting with {len(mapping)} known mappings")

# Known texts from screenshots paired with save states
targets = [
    ("Firstdialogue.p2s", "なあ、教えてくれよ～。俺、早くあの事を言わなきゃ、ならないんだよ。"),
    ("randomdialogue.p2s", "それでこうして時が過ぎていくのを、むなしく待っているのですか？"),
    ("greentext.p2s", "こちとら怪我人かかえてそんなひまなんてありゃしねえ"),
    ("greentextgnome.p2s", "おっ、なんだい、新米さんかい？俺はインゴってんだ、よろしくな。"),
    ("lotsoftextgnome.p2s", "難攻不落の城であろうと、鉄壁をほこる法王庁の宝物殿の中であろうとなんのその、"),
    ("knightguy.ps2.p2s", "聞いたかもしれないが、迷宮の第２階層において討伐隊のメンバーが消息を絶った。"),
    ("knighterguy.p2s", "君が、行方不明になったレジーナ達を探してくれる者かね。"),
    ("normaldungeonscreen.p2s", "特に変わったところはない"),
]

def search_ram_for_text(ram, known_text, existing_map):
    """Search 32MB RAM for a glyph buffer matching known_text using anchor glyphs."""
    text_len = len(known_text)
    
    # Build anchor positions: characters we already know the glyph for
    anchors = []
    for pos, char in enumerate(known_text):
        for glyph, mapped_char in existing_map.items():
            if mapped_char == char:
                anchors.append((pos, glyph, char))
                break
    
    if len(anchors) < 2:
        return None, "Not enough anchor glyphs"
    
    # Search RAM for regions where anchor glyphs appear at correct relative positions
    # Use the first two anchors as the primary search
    a1_pos, a1_glyph, a1_char = anchors[0]
    a2_pos, a2_glyph, a2_char = anchors[1]
    expected_gap = (a2_pos - a1_pos) * 2  # gap in bytes (uint16 = 2 bytes)
    
    candidates = []
    for addr in range(0x100000, len(ram) - text_len * 4, 2):
        val = struct.unpack_from("<H", ram, addr)[0]
        if val != a1_glyph:
            continue
        
        # Check second anchor at expected position
        addr2 = addr + expected_gap
        if addr2 + 2 > len(ram):
            continue
        val2 = struct.unpack_from("<H", ram, addr2)[0]
        if val2 != a2_glyph:
            continue
        
        # Check ALL anchors
        base = addr - a1_pos * 2
        if base < 0:
            continue
        
        all_match = True
        for pos, glyph, char in anchors:
            check_addr = base + pos * 2
            if check_addr + 2 > len(ram):
                all_match = False
                break
            check_val = struct.unpack_from("<H", ram, check_addr)[0]
            if check_val != glyph:
                all_match = False
                break
        
        if all_match:
            # Extract full glyph sequence
            glyphs = []
            for i in range(text_len):
                g = struct.unpack_from("<H", ram, base + i * 2)[0]
                glyphs.append(g)
            candidates.append((base, glyphs))
    
    # Filter: glyphs should be in reasonable range (0-2000) and no FFFF
    valid = []
    for base, glyphs in candidates:
        if all(0 <= g < 2000 for g in glyphs):
            valid.append((base, glyphs))
    
    if not valid:
        return None, f"No valid candidates ({len(candidates)} raw, anchors: {[(p,hex(g),c) for p,g,c in anchors[:5]]}"
    
    return valid[0], "OK"

new_total = 0
for save_file, known_text in targets:
    if not os.path.exists(save_file):
        log(f"\n--- {save_file}: FILE NOT FOUND ---")
        continue
    
    log(f"\n--- {save_file} ---")
    log(f"  Text: {known_text}")
    log(f"  Length: {len(known_text)} chars")
    
    try:
        zf = zipfile.ZipFile(save_file)
        ram = zf.read("eeMemory.bin")
    except Exception as e:
        log(f"  ERROR: {e}")
        continue
    
    result, status = search_ram_for_text(ram, known_text, mapping)
    
    if result is None:
        log(f"  {status}")
        continue
    
    base, glyphs = result
    log(f"  FOUND at RAM 0x{base:08X}!")
    
    # Build new mappings
    new_mappings = {}
    confirmed = 0
    conflicts = 0
    for glyph, char in zip(glyphs, known_text):
        if glyph in mapping:
            if mapping[glyph] == char:
                confirmed += 1
            else:
                conflicts += 1
                log(f"  CONFLICT: glyph {glyph} = {mapping[glyph]} vs {char}")
        else:
            new_mappings[glyph] = char
            mapping[glyph] = char
    
    log(f"  Confirmed: {confirmed}, New: {len(new_mappings)}, Conflicts: {conflicts}")
    new_total += len(new_mappings)
    
    if new_mappings:
        log(f"  New mappings:")
        for g, c in sorted(new_mappings.items()):
            log(f"    glyph {g:4d} (0x{g:04X}) = {c}")

# Save updated mapping
with open("data/msg_glyph_map.json", "w", encoding="utf-8") as f:
    json.dump({str(k): v for k, v in sorted(mapping.items())}, f, ensure_ascii=False, indent=2)

log(f"\n{'='*60}")
log(f"TOTAL: {len(mapping)} mappings ({new_total} new this run)")
hira = sum(1 for c in mapping.values() if "\u3040" <= c <= "\u309f")
kata = sum(1 for c in mapping.values() if "\u30a0" <= c <= "\u30ff")
kanji = sum(1 for c in mapping.values() if "\u4e00" <= c <= "\u9fff")
log(f"  Hiragana: {hira}")
log(f"  Katakana: {kata}")
log(f"  Kanji: {kanji}")
log(f"  Other: {len(mapping) - hira - kata - kanji}")
LOG.close()
