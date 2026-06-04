#!/usr/bin/env python3
"""
parse_chargen_resources.py -- Parse glyph streams in R1193-R1214 chargen resources
==================================================================================

FINDINGS:
  - R1193-R1214 are ALL dialogue/story resources for different chargen game states
  - They contain NO stat labels (体力/精神/etc) as glyph pairs in Section 2
  - Every resource starts with msg[0] = "階の主を倒避したメダルは奉神に捧け供った。"
    (a generic trophy/medal message)
  - The "stat label" kanji matches are ALL incidental uses in long dialogue text
  - Actual chargen stat/sidebar labels are rendered via R1272 menu font tiles
    (IDs 683-866) referenced from EXE menu struct records at 0x3C3000-0x3C5300

CHARGEN SCREEN ELEMENT MAP:
  - Sidebar labels (性別/種族/職業/属性) use tile pairs from menu_labels.csv:
    - 745+747 = 性別 (Gender)  [rows 31-32]
    - 749+751 = 種族 (Race)    [rows 33-34]
    - 753+755 = 属格 (Alignment) [rows 35-36]
    - 731+757 = 職業 (Class)   [rows 24,37]
  - Stat labels (体力/精神/etc) use single kanji glyph IDs from R1272:
    - IDs 346,535,717,308,354,320,718,696,582,719,590,720,721
    - These are individual chars rendered by the glyph system, NOT in MSG data

R1193-R1214 DIALOGUE RESOURCE MAP:
  R1193: 6,144B   3 msgs  Intro narrative (backstory)
  R1194: 8,192B   1 msgs  Extended backstory epilogue
  R1195: 2,048B   1 msgs  Empty/placeholder
  R1196: 106,496B 953 msgs  Main story dialogue bank (largest after R1203)
  R1197: 116,736B 1099 msgs Story dialogue bank (alternative paths?)
  R1198: 20,480B   88 msgs  Knight guild scenes
  R1199: 36,864B  254 msgs  Automata/Ortlinde scenes
  R1200: 47,104B  252 msgs  Teurgo/church scenes
  R1201: 26,624B  171 msgs  Conde/inn scenes
  R1202: 49,152B  300 msgs  Orc shop/entry scenes
  R1203: 169,984B 1633 msgs Largest bank - shop/guild/multi-scene
  R1204: 110,592B  999 msgs Story progression
  R1205: 100,352B  906 msgs Story progression
  R1206: 102,400B  914 msgs Story progression
  R1207: 102,400B  912 msgs Story progression
  R1208: 100,352B  907 msgs Dungeon lever/switch + story
  R1209: 75,776B  634 msgs  Yoppen/succubus scenes
  R1210: 90,112B  785 msgs  Story progression
  R1211: 77,824B  635 msgs  Story progression
  R1212: 86,016B  723 msgs  Story progression
  R1213: 22,528B   49 msgs  Dungeon story scenes
  R1214: 2,048B    1 msgs   Data placeholder
"""

import struct, os, json, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "extracted", "packdata_raw")
GLYPH_MAP_PATH = os.path.join(BASE, "data", "msg_glyph_map.json")

with open(GLYPH_MAP_PATH, "r", encoding="utf-8") as f:
    GLYPH_MAP = json.load(f)

MENU_TILE_START = 683

# Known stat/sidebar kanji glyph IDs (individual glyphs, NOT pairs)
STAT_GLYPH_IDS = {346, 535, 717, 308, 354, 320, 718, 696, 582, 719, 590, 720, 721}
SIDEBAR_GLYPH_IDS = {511, 512, 513, 514, 515, 504, 517}

# R1272 menu tile IDs for chargen sidebar (from menu_labels.csv)
CHARGEN_SIDEBAR_TILES = {
    731: "職(job)", 745: "性(sex)", 747: "別(separate)",
    749: "種(species)", 751: "族(clan)", 753: "属(belong)",
    755: "格(personality)", 757: "業(work)",
    759: "性別(gender-tile)", 760: "別(gender-tile2)",
}

# Known stat pair patterns (for BE uint16 adjacency search)
STAT_PAIRS = [
    (720, 346, "体力/HP"), (719, 590, "精神/MP"),
    (308, 354, "生命/VIT"), (320, 718, "素早/AGI"),
]
SIDEBAR_PAIRS = [
    (511, 512, "性別/Gender"), (513, 514, "種族/Race"),
    (515, 511, "属性/Alignment"), (504, 517, "職業/Class"),
]


def decode_glyph(gid):
    if gid == 0xFFFF:
        return "|"
    if gid == 0xFFFE:
        return "/"
    if gid >= 0xFB00:
        return f"<{gid:04X}>"
    s = GLYPH_MAP.get(str(gid))
    if s:
        return s
    return f"[{gid}]"


def decode_message(glyphs):
    return "".join(decode_glyph(g) for g in glyphs)


def parse_type02_resource(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    if len(data) < 0x1C:
        return None, []
    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", data, 0x18)[0]
    header_info = {
        "file_size": len(data),
        "sec2_size": sec2_size,
        "sec2_offset": sec2_offset,
    }
    if sec2_offset == 0 or sec2_offset >= len(data):
        return header_info, []
    sec2_end = min(sec2_offset + sec2_size, len(data))
    sec2_data = data[sec2_offset:sec2_end]
    n_words = len(sec2_data) // 2
    words = [struct.unpack_from(">H", sec2_data, i * 2)[0] for i in range(n_words)]
    groups = []
    msg_start = 0
    for wi in range(n_words):
        if words[wi] == 0xFFFF:
            groups.append(words[msg_start:wi])
            msg_start = wi + 1
    if msg_start < n_words:
        trailing = words[msg_start:]
        if any(w != 0x0000 for w in trailing):
            groups.append(trailing)
    header_info["num_groups"] = len(groups)
    return header_info, groups


def main():
    print("=" * 78)
    print("  CHARGEN RESOURCE PARSER -- R1193-R1214")
    print("=" * 78)

    # Overview
    print("\n--- OVERVIEW ---\n")
    print(f"{'RES':>5} {'SIZE':>8} {'SEC2off':>8} {'SEC2sz':>8} {'MSGS':>5}  CONTENT SUMMARY")
    print("-" * 78)

    all_data = {}
    for res_id in range(1193, 1215):
        filename = f"{res_id:04d}_type02.raw"
        filepath = os.path.join(RAW_DIR, filename)
        if not os.path.isfile(filepath):
            print(f"{res_id:>5}  -- file not found --")
            continue
        header, groups = parse_type02_resource(filepath)
        all_data[res_id] = (header, groups)

        n_msgs = len(groups)
        sz = header["file_size"]
        s2off = header["sec2_offset"]
        s2sz = header["sec2_size"]

        # Classify content
        n_menu_tile_msgs = 0
        n_ctrl_only = 0
        has_choice = False
        first_msg_preview = ""

        for gi, g in enumerate(groups):
            text_only = [x for x in g if x < 0xFB00 and x != 0xFFFE]
            if any(x >= MENU_TILE_START and x < 867 for x in text_only):
                n_menu_tile_msgs += 1
            if all(x >= 0xFB00 or x == 0xFFFE for x in g) and g:
                n_ctrl_only += 1
            if any(x == 0xFFC0 for x in g):
                has_choice = True
            if gi == 0 and g:
                first_msg_preview = decode_message(g)[:40]

        notes = first_msg_preview
        if has_choice:
            notes += " [CHOICES]"

        print(f"{res_id:>5} {sz:>8,} {s2off:>#8x} {s2sz:>8,} {n_msgs:>5}  {notes}")

    # Stat pair adjacency search
    print("\n\n--- STAT/SIDEBAR PAIR SEARCH (adjacent BE uint16 in Section 2) ---")
    print("  Searching for: 体力, 精神, 生命, 素早, 性別, 種族, 属性, 職業")

    found_any = False
    for res_id in sorted(all_data.keys()):
        header, groups = all_data[res_id]
        for msg_idx, glyphs in enumerate(groups):
            for i in range(len(glyphs) - 1):
                for g1, g2, name in STAT_PAIRS + SIDEBAR_PAIRS:
                    if glyphs[i] == g1 and glyphs[i + 1] == g2:
                        decoded = decode_message(glyphs)
                        length = len(glyphs)
                        is_label = length <= 6
                        tag = "*** LABEL ***" if is_label else "dialogue"
                        print(f"  R{res_id} msg[{msg_idx}] {name} ({tag}, {length}g): {decoded[:80]}")
                        found_any = True

    if not found_any:
        print("  >>> NO MATCHES FOUND <<<")
        print("  Stat labels are NOT stored as glyph pairs in R1193-R1214 Section 2 data.")
        print("  They are rendered via R1272 menu font tiles + EXE menu struct records.")

    # Chargen sidebar tile search
    print("\n\n--- CHARGEN SIDEBAR TILE USAGE (R1272 tiles 731,745,747,749,751,753,755,757) ---")
    sidebar_tile_ids = set(CHARGEN_SIDEBAR_TILES.keys())

    for res_id in sorted(all_data.keys()):
        header, groups = all_data[res_id]
        matches = []
        for msg_idx, glyphs in enumerate(groups):
            text_only = [g for g in glyphs if g < 0xFB00 and g != 0xFFFE]
            hits = [g for g in text_only if g in sidebar_tile_ids]
            if hits:
                decoded = decode_message(glyphs)
                matches.append((msg_idx, hits, decoded, len(glyphs)))

        if matches:
            print(f"\n  R{res_id} ({len(matches)} messages with sidebar tiles):")
            for msg_idx, hits, decoded, length in matches[:5]:
                hit_names = [CHARGEN_SIDEBAR_TILES[h] for h in hits]
                tag = "SHORT/LABEL" if length <= 8 else "dialogue"
                print(f"    msg[{msg_idx:3d}] ({length:3d}g, {tag}) tiles={hit_names}")
                print(f"           {decoded[:80]}")
            if len(matches) > 5:
                print(f"    ... +{len(matches) - 5} more")

    # Section 1 opcode data analysis for chargen resources
    print("\n\n--- SECTION 1 (OPCODE) ANALYSIS ---")
    print("  Section 1 contains scripts/opcodes that control which messages are displayed.")
    print("  The chargen stat screen is likely driven by Section 1 opcodes that reference")
    print("  individual glyph IDs, NOT by Section 2 glyph stream messages.")

    for res_id in sorted(all_data.keys()):
        header, groups = all_data[res_id]
        filepath = os.path.join(RAW_DIR, f"{res_id:04d}_type02.raw")
        with open(filepath, "rb") as f:
            data = f.read()

        s2off = header.get("sec2_offset", 0)
        sec1_size = s2off
        sec2_size = header.get("sec2_size", 0)
        after_sec2 = len(data) - (s2off + sec2_size)

        print(f"  R{res_id}: sec1={sec1_size:,}B  sec2={sec2_size:,}B  after_sec2={after_sec2:,}B")

    # Final summary
    print("\n\n" + "=" * 78)
    print("  CONCLUSION")
    print("=" * 78)
    print("""
  R1193-R1214 are STORY/DIALOGUE resources for different chargen game states.
  They do NOT contain chargen stat screen labels as glyph data.

  The chargen stat screen labels (体力, 精神, 生命, etc.) are rendered via:
    1. R1272 menu font atlas - individual glyph tiles
    2. EXE menu struct records at 0x3C3000-0x3C5300 (56 bytes each, 2 glyph slots)
    3. Individual kanji glyph IDs (346, 535, 717, etc.) from the R1272 font

  The chargen sidebar labels (性別, 種族, 職業, 属性) use tile pairs:
    - 745+747 = 性別 (Gender)    [menu_labels.csv rows 31-32]
    - 749+751 = 種族 (Race)      [menu_labels.csv rows 33-34]
    - 753+755 = 属格 (Alignment) [menu_labels.csv rows 35-36]
    - 731+757 = 職業 (Class)     [menu_labels.csv rows 24,37]

  R1188 NOT being read by the game (confirmed by XOR test) means the name
  entry screen uses a DIFFERENT font resource, likely loaded from the EXE
  or a different PACKDATA resource.

  To translate chargen stat labels: modify R1272 font tiles + EXE struct records.
  R1193-R1214 need translation as regular dialogue resources.
""")


if __name__ == "__main__":
    main()
