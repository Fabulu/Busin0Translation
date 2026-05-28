import sys, io, struct, json, zipfile, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
LOG = open("dumps/batch_xref_be_log.txt", "w", encoding="utf-8")
def log(msg):
    LOG.write(msg + "\n"); LOG.flush(); print(msg)

mapping = {int(k): v for k, v in json.load(open("data/msg_glyph_map.json", encoding="utf-8")).items()}
log(f"Starting with {len(mapping)} known mappings")

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

def search_ram_be(ram, known_text, existing_map):
    text_len = len(known_text)
    anchors = []
    for pos, char in enumerate(known_text):
        for glyph, mapped_char in existing_map.items():
            if mapped_char == char:
                anchors.append((pos, glyph, char))
                break
    if len(anchors) < 2:
        return None, f"Only {len(anchors)} anchors"
    
    a1_pos, a1_glyph, _ = anchors[0]
    a2_pos, a2_glyph, _ = anchors[1]
    gap = (a2_pos - a1_pos) * 2  # bytes between anchors (BE uint16 = 2 bytes each)
    
    candidates = []
    for addr in range(0x100000, len(ram) - text_len * 2, 2):
        val = struct.unpack_from(">H", ram, addr)[0]  # BIG ENDIAN!
        if val != a1_glyph:
            continue
        addr2 = addr + gap
        if addr2 + 2 > len(ram):
            continue
        val2 = struct.unpack_from(">H", ram, addr2)[0]
        if val2 != a2_glyph:
            continue
        
        base = addr - a1_pos * 2
        if base < 0:
            continue
        
        all_match = True
        for pos, glyph, _ in anchors:
            check = base + pos * 2
            if check + 2 > len(ram):
                all_match = False; break
            if struct.unpack_from(">H", ram, check)[0] != glyph:
                all_match = False; break
        
        if all_match:
            glyphs = [struct.unpack_from(">H", ram, base + i*2)[0] for i in range(text_len)]
            if all(0 <= g < 2000 for g in glyphs):
                candidates.append((base, glyphs))
    
    if not candidates:
        return None, f"0 matches ({len(anchors)} anchors used)"
    return candidates[0], "OK"

new_total = 0
for save_file, known_text in targets:
    if not os.path.exists(save_file):
        log(f"\n--- {save_file}: NOT FOUND ---"); continue
    log(f"\n--- {save_file} ---")
    log(f"  Text: {known_text} ({len(known_text)} chars)")
    
    try:
        ram = zipfile.ZipFile(save_file).read("eeMemory.bin")
    except Exception as e:
        log(f"  ERROR: {e}"); continue
    
    result, status = search_ram_be(ram, known_text, mapping)
    if result is None:
        log(f"  {status}"); continue
    
    base, glyphs = result
    log(f"  FOUND at 0x{base:08X}!")
    
    new_maps = {}
    confirmed = 0
    conflicts = 0
    for g, c in zip(glyphs, known_text):
        if g in mapping:
            if mapping[g] == c: confirmed += 1
            else: conflicts += 1; log(f"  CONFLICT: {g}={mapping[g]} vs {c}")
        else:
            new_maps[g] = c; mapping[g] = c
    
    log(f"  Confirmed: {confirmed}, New: {len(new_maps)}, Conflicts: {conflicts}")
    new_total += len(new_maps)
    for g, c in sorted(new_maps.items()):
        log(f"    {g:4d} (0x{g:04X}) = {c}")

with open("data/msg_glyph_map.json", "w", encoding="utf-8") as f:
    json.dump({str(k): v for k, v in sorted(mapping.items())}, f, ensure_ascii=False, indent=2)

log(f"\n{'='*60}")
log(f"TOTAL: {len(mapping)} mappings ({new_total} new)")
hira = sum(1 for c in mapping.values() if "\u3040" <= c <= "\u309f")
kata = sum(1 for c in mapping.values() if "\u30a0" <= c <= "\u30ff")
kanji = sum(1 for c in mapping.values() if "\u4e00" <= c <= "\u9fff")
log(f"  Hiragana: {hira}, Katakana: {kata}, Kanji: {kanji}, Other: {len(mapping)-hira-kata-kanji}")
LOG.close()
