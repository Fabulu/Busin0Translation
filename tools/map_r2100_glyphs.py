#!/usr/bin/env python3
"""
Map all glyphs in R2100 (chargen/name-entry font atlas).

R2100 is a type-04 resource at PACKDATA.DIG byte offset 34816, size 139264 bytes.
It contains 4 sub-blocks of 256x256 PSMT4 textures (16x16 cells = 256 glyphs each).

Structure per resource:
  - 64-byte TOC (4 entries: index, size=34624, offset)
  - 4 x sub-block (34624 bytes each):
      - 1216-byte GIF/DMA header
      - 32768-byte PSMT4 pixel data (256x256, 4bpp)
      - 640-byte CLUT (10 palettes x 16 RGBA entries)

Deswizzle params: dbw_ct32=128, bw_psmt4=256 (256x256 PSMT4)

Glyph layout:
  - Palette index 15 = transparent (background)
  - Palette indices 0-14 = ink (glyph pixels, 0=darkest)
  - "ink count" = pixels with value < 15
  - Sub-block 0: ASCII (cell+0x20) + Japanese kana
  - Sub-blocks 1-3: Kanji
"""
import os
import sys
import struct
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKDATA_PATH = os.path.join(BASE, "extracted", "PACKDATA.DIG")
OUT_DIR = os.path.join(BASE, "build", "textures_to_edit", "r2100")

# R2100 location in PACKDATA.DIG
R2100_OFFSET = 34816       # byte 34816 = sector 17 * 2048
R2100_SIZE = 139264         # 68 sectors * 2048

# Sub-block layout
TOC_SIZE = 64
SUB_BLOCK_SIZE = 34624
HEADER_SIZE = 1216          # GIF/DMA header per sub-block
PIXEL_SIZE = 32768          # 256*256/2 bytes PSMT4
CLUT_SIZE = 640             # 10 palettes * 16 colors * 4 bytes

# Texture dimensions
TEX_W = 256
TEX_H = 256
CELL_W = 16
CELL_H = 16
COLS = TEX_W // CELL_W      # 16
ROWS = TEX_H // CELL_H      # 16
CELLS_PER_BLOCK = COLS * ROWS  # 256

# Deswizzle parameters
DBW_CT32 = 128
BW_PSMT4 = 256

# ---- Known glyph ordering for sub-block 0 ----
# Verified by visual inspection of deswizzled atlas images at 4x zoom.
#
# Cells 0-58: Standard ASCII 0x20 (space) through 0x5A (Z)
# Cells 59-63: Japanese punctuation (not ASCII [ \ ] ^ _)
# Cell 64: space (blank)
# Cells 65-90: lowercase a-z
# Cells 91-95: Special symbols (not ASCII { | } ~)
# Cells 96-111: Roman numerals I-X, then symbols
# Cells 112-255: Japanese kana (hiragana, then katakana with variants)

# Special overrides for cells that look like ASCII but aren't:
SPECIAL_CHARS = {
    59: "「",   # not [
    60: "▲",   # not backslash (filled triangle)
    61: "」",   # not ]
    62: "、",   # not ^  (Japanese comma)
    63: "。",   # not _  (Japanese period)
    91: "・",   # not {  (nakaguro/middle dot)
    92: "…",   # not |  (ellipsis)
    93: "ー",   # not }  (prolonged sound mark)
    94: "～",   # not ~  (wave dash)
    95: "★",   # star symbol
}

# Cells 96-111: Roman numerals and symbols
ROMAN_AND_SYMBOLS = {
    96:  "I",    # Roman numeral 1
    97:  "II",   # Roman numeral 2
    98:  "III",  # Roman numeral 3
    99:  "IV",   # Roman numeral 4
    100: "V",    # Roman numeral 5
    101: "VI",   # Roman numeral 6
    102: "VII",  # Roman numeral 7
    103: "VIII", # Roman numeral 8
    104: "IX",   # Roman numeral 9
    105: "X",    # Roman numeral 10
    106: "○",   # circle
    107: "×",   # cross/multiply
    108: "←",   # left arrow
    109: "→",   # right arrow
    110: "↑",   # up arrow  (faint, but present)
    111: "▼",   # down-pointing filled triangle
}

# Cells 112-255: Japanese kana
# Row 7 (112-127): hiragana あ-た
# Row 8 (128-143): hiragana ち-み
# Row 9 (144-159): hiragana む-ん + dakuten が ぎ
# Row A (160-175): hiragana dakuten ぐ-ぶ
# Row B (176-191): hiragana dakuten/handakuten べ-っ (small tsu)
# Row C (192-207): katakana ヴ ア-ソ
# Row D (208-223): katakana タ-マ
# Row E (224-239): katakana ミ-ガ
# Row F (240-255): katakana dakuten ギ-ビ

KANA_MAP = {
    # Row 7: hiragana basic (cells 112-127)
    112: "あ", 113: "い", 114: "う", 115: "え", 116: "お",
    117: "か", 118: "き", 119: "く", 120: "け", 121: "こ",
    122: "さ", 123: "し", 124: "す", 125: "せ", 126: "そ", 127: "た",
    # Row 8: hiragana basic (cells 128-143)
    128: "ち", 129: "つ", 130: "て", 131: "と", 132: "な",
    133: "に", 134: "ぬ", 135: "ね", 136: "の", 137: "は",
    138: "ひ", 139: "ふ", 140: "へ", 141: "ほ", 142: "ま", 143: "み",
    # Row 9: hiragana (cells 144-159)
    144: "む", 145: "め", 146: "も", 147: "や", 148: "ゆ",
    149: "よ", 150: "ら", 151: "り", 152: "る", 153: "れ",
    154: "ろ", 155: "わ", 156: "を", 157: "ん", 158: "が", 159: "ぎ",
    # Row A (10): hiragana dakuten (cells 160-175)
    160: "ぐ", 161: "げ", 162: "ご", 163: "ざ", 164: "じ",
    165: "ず", 166: "ぜ", 167: "ぞ", 168: "だ", 169: "ぢ",
    170: "づ", 171: "で", 172: "ど", 173: "ば", 174: "び", 175: "ぶ",
    # Row B (11): hiragana dakuten/handakuten + small kana (cells 176-191)
    176: "べ", 177: "ぼ", 178: "ぱ", 179: "ぴ", 180: "ぷ",
    181: "ぺ", 182: "ぽ", 183: "ゃ", 184: "ゅ", 185: "ょ",
    186: "ぁ", 187: "ぃ", 188: "ぅ", 189: "ぇ", 190: "ぉ", 191: "っ",
    # Row C (12): katakana basic (cells 192-207)
    192: "ヴ", 193: "ア", 194: "イ", 195: "ウ", 196: "エ",
    197: "オ", 198: "カ", 199: "キ", 200: "ク", 201: "ケ",
    202: "コ", 203: "サ", 204: "シ", 205: "ス", 206: "セ", 207: "ソ",
    # Row D (13): katakana basic (cells 208-223)
    208: "タ", 209: "チ", 210: "ツ", 211: "テ", 212: "ト",
    213: "ナ", 214: "ニ", 215: "ヌ", 216: "ネ", 217: "ノ",
    218: "ハ", 219: "ヒ", 220: "フ", 221: "ヘ", 222: "ホ", 223: "マ",
    # Row E (14): katakana basic + first dakuten (cells 224-239)
    224: "ミ", 225: "ム", 226: "メ", 227: "モ", 228: "ヤ",
    229: "ユ", 230: "ヨ", 231: "ラ", 232: "リ", 233: "ル",
    234: "レ", 235: "ロ", 236: "ワ", 237: "ヲ", 238: "ン", 239: "ガ",
    # Row F (15): katakana dakuten (cells 240-255)
    240: "ギ", 241: "グ", 242: "ゲ", 243: "ゴ", 244: "ザ",
    245: "ジ", 246: "ズ", 247: "ゼ", 248: "ゾ", 249: "ダ",
    250: "ヂ", 251: "ヅ", 252: "デ", 253: "ド", 254: "バ", 255: "ビ",
}


# ---- Complete kanji mapping for sub-blocks 1-3 ----
# Each sub-block has 256 cells (16 rows x 16 cols).
# Read cell-by-cell from 5x zoom images of each row.

BLOCK1_KANJI = (
    # Row 0 (cells 0-15): katakana continuation from block 0
    "ブベボパピプペポヤユヨアイウエオ"
    # Row 1 (cells 16-31)
    "ッヴ剣小手鎧盾斧魔呪皮鎖聖護戦者"
    # Row 2 (cells 32-47)
    "刀悪杖飾弓胸兜大王士裏符神輪指髪"
    # Row 3 (cells 48-63)
    "騎狂切魂信忍石邪血死名盗武炎工人"
    # Row 4 (cells 64-79)
    "心風落真亡霊法短上賊精雷装夜壊極"
    # Row 5 (cells 80-95)
    "六中一気立不術師背白力骨光女撃化"
    # Row 6 (cells 96-111)
    "息黒仰殺正字外銀斬竜鬼裂退二影行"
    # Row 7 (cells 112-127)
    "冷見失与苦災対道示滅闇転星傷癒長"
    # Row 8 (cells 128-143)
    "逆天幻重文疾閃代十頭乱束教毒帰太"
    # Row 9 (cells 144-159)
    "刃侍支水像司封八紅赤秘村移復子回"
    # Row 10 (cells 160-175)
    "凍妖堕金食合古良月静憎刑定角祈耐"
    # Row 11 (cells 176-191)
    "貫質破守砕禁染吹万寂七投視惑福嘆"
    # Row 12 (cells 192-207)
    "塵速病宗菊狩章廻巾奈彫歪執縫琥珀"
    # Row 13 (cells 208-223)
    "玄腿紋幡鋼殻胴船虎徹兼容窒塗獅又"
    # Row 14 (cells 224-239)
    "棍悶剛羅刹鎌冒険君専用台帳開休量"
    # Row 15 (cells 240-255)
    "所出新規登録詳細職改抹消編成前性"
)

BLOCK2_KANJI = (
    # Row 0 (cells 0-15)
    "別種族属格業男間善飽保約家孤独的"
    # Row 1 (cells 16-31)
    "社交収集慎義感知存電迷友愛源費本"
    # Row 2 (cells 32-47)
    "当御方権限参加乙分屋愚鈍研究抜差"
    # Row 3 (cells 48-63)
    "好色自盾勝再熱漢負嫌止際何宮探索"
    # Row 4 (cells 64-79)
    "同時街戻機物敏援銭奴安理由過度認"
    # Row 5 (cells 80-95)
    "勢囲動腰少数着協流望備品耗捨無稼"
    # Row 6 (cells 96-111)
    "闘溶思例意許多操画明考習得強常計"
    # Row 7 (cells 112-127)
    "求危憶未世界修表個初来事反応範平"
    # Row 8 (cells 128-143)
    "和込判断欠牽買使深絆野蛮変全読射"
    # Row 9 (cells 144-159)
    "誰喜緒怒希発日標元損異関持興味身"
    # Row 10 (cells 160-175)
    "体快陣覚仲識他解除居敗斉美追粗末"
    # Row 11 (cells 176-191)
    "走潜番優敵今罪柱命市終雇能団日経"
    # Row 12 (cells 192-207)
    "可現在選択必要値足音順低高恵生捷"
    # Row 13 (cells 208-223)
    "幸運攻率防避僧侶入振鍛隠密将軍怪"
    # Row 14 (cells 224-239)
    "英決個基豊盤々薄焼溢弱扱右言素早"
    # Row 15 (cells 240-255)
    "向厚点城柄軽後形近秩序混沌地年隊"
)

BLOCK3_KANJI = (
    # Row 0 (cells 0-15)
    "列威易下果確活鑑器稀技急響具系功"
    # Row 1 (cells 16-31)
    "効抗仕就唱浄絶打抵内難扉罠離脱先"
    # Row 2 (cells 32-47)
    "替記号羽液牙巨昆糸歯耳首尻折舌臓"
    # Row 3 (cells 48-63)
    "虫鳥爪笛瞳肉猫粘馬尾面毛翼卵涙狼"
    # Row 4 (cells 64-79)
    "腕還治玉宝埋薬放両片宿場泊部空服"
    # Row 5 (cells 80-95)
    "棒恐怖満作材組換去突然逃忘冥府呼"
    # Row 6 (cells 96-111)
    "声吐補助連携各衛位置相回始紙触更"
    # Row 7 (cells 112-127)
    "健康刺寺院我寄付忠達越療頼並級最"
    # Row 8 (cells 128-143)
    "吸走杯掲板引受士商売練医残念景整"
    # Row 9 (cells 144-159)
    "布調採遺産永遠朽待忠実兵蟲直接続"
    # Row 10 (cells 160-175)
    "抽購額完岩荷簡期乗客頻激車散似謝"
    # Row 11 (cells 176-191)
    "取住情設倉送増第派単築注店穴納配"
    # Row 12 (cells 192-207)
    "販晶評討便報民務利了伐毎通縮甲尖"
    # Row 13 (cells 208-223)
    "半麻階段睡灰憑泉議酒眠氷即箱視奇"
    # Row 14 (cells 224-239)
    "跡昇以有床員枚依酬競倒減状態特殊"
    # Row 15 (cells 240-255)
    "奪恋輝制姿歴書描広国熱型侵市暗却"
)

# Stat label kanji positions (sub-block, row, col, cell, global_index)
# Stat label kanji: (sub_block, row, col) -> cell = row*16+col, global = sb*256+cell
STAT_KANJI_POSITIONS = {
    "力": (1,  5, 10),  # block1 row5 col10  -> cell 90,  global 346
    "知": (2,  1,  7),  # block2 row1 col7   -> cell 23,  global 535
    "恵": (2, 12, 13),  # block2 row12 col13 -> cell 205, global 717
    "信": (1,  3,  4),  # block1 row3 col4   -> cell 52,  global 308
    "仰": (1,  6,  2),  # block1 row6 col2   -> cell 98,  global 354
    "心": (1,  4,  0),  # block1 row4 col0   -> cell 64,  global 320
    "生": (2, 12, 14),  # block2 row12 col14 -> cell 206, global 718
    "命": (2, 11,  8),  # block2 row11 col8  -> cell 184, global 696
    "敏": (2,  4,  6),  # block2 row4 col6   -> cell 70,  global 582
    "捷": (2, 12, 15),  # block2 row12 col15 -> cell 207, global 719
    "度": (2,  4, 14),  # block2 row4 col14  -> cell 78,  global 590
    "幸": (2, 13,  0),  # block2 row13 col0  -> cell 208, global 720
    "運": (2, 13,  1),  # block2 row13 col1  -> cell 209, global 721
}


def read_r2100():
    """Read R2100 raw data from PACKDATA.DIG."""
    with open(PACKDATA_PATH, "rb") as f:
        f.seek(R2100_OFFSET)
        data = f.read(R2100_SIZE)
    assert len(data) == R2100_SIZE, f"Short read: {len(data)} vs {R2100_SIZE}"
    return data


def parse_toc(data):
    """Parse the 64-byte TOC at the start of R2100."""
    entries = []
    for i in range(4):
        off = i * 16
        idx, size, file_off, _ = struct.unpack_from("<IIII", data, off)
        entries.append({"index": idx, "size": size, "offset": file_off})
        print(f"  TOC[{i}]: index={idx}, size={size}, offset=0x{file_off:X}")
    return entries


def extract_sub_block(data, toc_entry):
    """Extract pixel data and palette from a sub-block."""
    sb_off = toc_entry["offset"]
    sb_size = toc_entry["size"]

    pixel_data = data[sb_off + HEADER_SIZE : sb_off + HEADER_SIZE + PIXEL_SIZE]
    clut_data = data[sb_off + HEADER_SIZE + PIXEL_SIZE : sb_off + sb_size]

    assert len(pixel_data) == PIXEL_SIZE, f"pixel_data: {len(pixel_data)} vs {PIXEL_SIZE}"

    # Extract first palette (16 RGBA entries = 64 bytes) from CLUT
    palette = bytearray(clut_data[:64]) if len(clut_data) >= 64 else bytearray(64)

    return pixel_data, palette


def deswizzle_sub_block(pixel_data):
    """Deswizzle PSMT4 pixel data to linear pixel indices."""
    return deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                           bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)


def make_image(pixels, palette):
    """Create RGBA image from deswizzled pixels and palette."""
    img = Image.new("RGBA", (TEX_W, TEX_H))
    pal_colors = []
    for i in range(16):
        r = palette[i * 4]
        g = palette[i * 4 + 1]
        b = palette[i * 4 + 2]
        a = min(palette[i * 4 + 3] * 2, 255)  # PS2 alpha 0-128 -> 0-255
        pal_colors.append((r, g, b, a))

    img_data = [pal_colors[min(p, 15)] for p in pixels[:TEX_W * TEX_H]]
    img.putdata(img_data)
    return img


def measure_ink(pixels, row, col):
    """Count ink pixels (value < 15) in a 16x16 cell.
    Palette index 15 = transparent background, 0-14 = visible glyph ink.
    """
    count = 0
    for cy in range(CELL_H):
        for cx in range(CELL_W):
            px = col * CELL_W + cx
            py = row * CELL_H + cy
            if pixels[py * TEX_W + px] < 15:
                count += 1
    return count


def draw_labeled_grid(img, sub_block_idx, ink_counts, char_map=None):
    """Draw grid lines and cell index labels on the image.

    char_map: optional dict mapping cell_index -> character string
    """
    scale = 3
    label_margin = 24
    out_w = TEX_W * scale + label_margin
    out_h = TEX_H * scale + label_margin

    out = Image.new("RGBA", (out_w, out_h), (32, 32, 32, 255))

    # Paste scaled image (with black background for visibility)
    bg = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 255))
    bg.paste(img, (0, 0), img)
    scaled = bg.resize((TEX_W * scale, TEX_H * scale), Image.NEAREST)
    out.paste(scaled, (label_margin, label_margin))

    draw = ImageDraw.Draw(out)

    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except (OSError, IOError):
        font = ImageFont.load_default()

    try:
        font_small = ImageFont.truetype("arial.ttf", 8)
    except (OSError, IOError):
        font_small = font

    # Draw grid lines
    for r in range(ROWS + 1):
        y = label_margin + r * CELL_H * scale
        draw.line([(label_margin, y), (out_w, y)], fill=(80, 80, 80, 200), width=1)
    for c in range(COLS + 1):
        x = label_margin + c * CELL_W * scale
        draw.line([(x, label_margin), (x, out_h)], fill=(80, 80, 80, 200), width=1)

    # Label rows and columns
    for r in range(ROWS):
        y = label_margin + r * CELL_H * scale + (CELL_H * scale) // 2 - 5
        draw.text((2, y), f"{r:X}", fill=(200, 200, 200, 255), font=font_small)
    for c in range(COLS):
        x = label_margin + c * CELL_W * scale + (CELL_W * scale) // 2 - 4
        draw.text((x, 2), f"{c:X}", fill=(200, 200, 200, 255), font=font_small)

    # Label each cell with its index
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            ink = ink_counts[idx]
            x = label_margin + c * CELL_W * scale + 2
            y = label_margin + r * CELL_H * scale + 2

            if ink > 0:
                color = (255, 255, 0, 255)  # yellow for occupied
            else:
                color = (60, 60, 60, 255)  # dim for empty

            draw.text((x, y), f"{idx}", fill=color, font=font_small)

    # Title
    occupied = sum(1 for d in ink_counts if d > 0)
    draw.text((label_margin, out_h - 14),
              f"Sub-block {sub_block_idx} | Glyphs: {occupied}/256",
              fill=(255, 255, 255, 255), font=font_small)

    return out


def build_block0_charmap(ink_counts):
    """Build character map for sub-block 0."""
    charmap = {}

    # Cells 0-58: ASCII 0x20-0x5A (space through Z)
    for i in range(59):
        code = i + 0x20
        if 0x20 <= code <= 0x7E:
            charmap[i] = chr(code)

    # Cells 59-63: Japanese punctuation (overrides)
    charmap.update(SPECIAL_CHARS)

    # Cell 64: space (blank)
    charmap[64] = " "

    # Cells 65-90: lowercase a-z
    for i in range(65, 91):
        charmap[i] = chr(i - 65 + ord('a'))

    # Cells 91-95: handled by SPECIAL_CHARS above

    # Cells 96-111: Roman numerals and symbols
    charmap.update(ROMAN_AND_SYMBOLS)

    # Cells 112-255: Japanese kana
    charmap.update(KANA_MAP)

    # Report unmapped occupied cells
    unmapped = []
    for i in range(256):
        if ink_counts[i] > 0 and i not in charmap:
            unmapped.append(i)

    if unmapped:
        print(f"  WARNING: {len(unmapped)} occupied cells unmapped: {unmapped}")
    else:
        print(f"  All {sum(1 for d in ink_counts if d > 0)} occupied cells mapped!")

    return charmap


def build_kanji_charmap(sb_idx, kanji_str):
    """Build character map for a kanji sub-block from its string."""
    charmap = {}
    chars = list(kanji_str)
    for i, ch in enumerate(chars):
        if i < 256:
            charmap[i] = ch
    return charmap


def create_composite(grid_images, all_ink):
    """Create composite image showing all 4 sub-blocks with labels."""
    w = grid_images[0].width
    h = grid_images[0].height
    margin = 20

    comp_w = w * 2 + margin * 3
    comp_h = h * 2 + margin * 3 + 30

    comp = Image.new("RGBA", (comp_w, comp_h), (16, 16, 16, 255))
    draw = ImageDraw.Draw(comp)

    try:
        title_font = ImageFont.truetype("arial.ttf", 14)
    except (OSError, IOError):
        title_font = ImageFont.load_default()

    positions = [
        (margin, margin + 20),
        (margin + w + margin, margin + 20),
        (margin, margin + h + margin + 20),
        (margin + w + margin, margin + h + margin + 20),
    ]

    labels = [
        "Block 0: ASCII + Kana",
        "Block 1: Kanji page 1",
        "Block 2: Kanji page 2",
        "Block 3: Kanji page 3",
    ]

    for i, (img, (px, py)) in enumerate(zip(grid_images, positions)):
        comp.paste(img, (px, py))
        occ = sum(1 for d in all_ink[i] if d > 0)
        draw.text((px, py - 16),
                  f"{labels[i]} ({occ} glyphs)",
                  fill=(255, 200, 100, 255), font=title_font)

    draw.text((margin, 2),
              "R2100 Chargen Font Atlas - All Sub-blocks (256x256 PSMT4, 16x16 cells)",
              fill=(255, 255, 255, 255), font=title_font)

    total = sum(sum(1 for d in dd if d > 0) for dd in all_ink)
    draw.text((comp_w - 300, comp_h - 18),
              f"Total glyphs: {total}/1024",
              fill=(200, 255, 200, 255), font=title_font)

    return comp


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("=== R2100 Glyph Mapper ===\n")

    # Step 1: Read R2100
    print("Reading R2100 from PACKDATA.DIG...")
    r2100_data = read_r2100()
    print(f"  Read {len(r2100_data)} bytes from offset {R2100_OFFSET}\n")

    # Step 2: Parse TOC
    print("Parsing TOC:")
    toc = parse_toc(r2100_data)
    print()

    all_pixels = []
    all_ink = []
    all_images = []
    grid_images = []

    for sb_idx in range(4):
        print(f"--- Sub-block {sb_idx} ---")

        # Extract pixel data and palette
        pixel_data, palette = extract_sub_block(r2100_data, toc[sb_idx])
        print(f"  Extracted {len(pixel_data)} pixel bytes + {len(palette)} palette bytes")

        # Deswizzle
        print(f"  Deswizzling (dbw_ct32={DBW_CT32}, bw_psmt4={BW_PSMT4})...")
        pixels = deswizzle_sub_block(pixel_data)
        all_pixels.append(pixels)

        # Make image
        img = make_image(pixels, palette)
        all_images.append(img)

        # Save raw deswizzled image
        raw_path = os.path.join(OUT_DIR, f"r2100_block{sb_idx}_raw.png")
        # Save with black background for visibility
        bg = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 255))
        bg.paste(img, (0, 0), img)
        bg.save(raw_path)
        print(f"  Saved raw: {raw_path}")

        # Measure ink per cell
        ink_counts = []
        for r in range(ROWS):
            for c in range(COLS):
                ink = measure_ink(pixels, r, c)
                ink_counts.append(ink)
        all_ink.append(ink_counts)

        occupied = sum(1 for d in ink_counts if d > 0)
        print(f"  Occupied cells (ink>0): {occupied}/256")

        # Print ink density map
        print("  Ink density map ('.' = empty, 1-9 = ink level):")
        for r in range(ROWS):
            row_str = "    "
            for c in range(COLS):
                d = ink_counts[r * COLS + c]
                if d == 0:
                    row_str += ".  "
                else:
                    level = min(9, max(1, d // 12))
                    row_str += f"{level}  "
            print(f"  Row {r:2d}: {row_str}")

        # Create labeled grid image
        grid_img = draw_labeled_grid(img, sb_idx, ink_counts)
        grid_images.append(grid_img)

        grid_path = os.path.join(OUT_DIR, f"r2100_block{sb_idx}_grid.png")
        grid_img.save(grid_path)
        print(f"  Saved grid: {grid_path}")
        print()

    # ---- Build all character maps ----
    print("=== Character Mapping ===")

    # Block 0: ASCII + kana
    print("\n  Sub-block 0: ASCII + Kana")
    charmap0 = build_block0_charmap(all_ink[0])

    # Blocks 1-3: Kanji
    kanji_strings = [BLOCK1_KANJI, BLOCK2_KANJI, BLOCK3_KANJI]
    charmap_all = [charmap0]
    for sb_idx in range(1, 4):
        cm = build_kanji_charmap(sb_idx, kanji_strings[sb_idx - 1])
        charmap_all.append(cm)
        mapped = sum(1 for i in range(256) if i in cm and all_ink[sb_idx][i] > 0)
        print(f"  Sub-block {sb_idx}: {mapped} kanji mapped, "
              f"string length={len(kanji_strings[sb_idx-1])}")

    # Print block 0 ASCII portion (compact)
    print("\n  Block 0 - ASCII cells 0-58 (space through Z):")
    for r in range(4):
        chars = []
        for c in range(COLS):
            idx = r * COLS + c
            if idx < 59:
                ch = charmap0.get(idx, " ")
                chars.append(ch if ch.strip() else ".")
        print(f"    Row {r}: {' '.join(chars)}")

    print("  Block 0 - Special chars 59-63: "
          + " ".join(f"{charmap0.get(i,'?')}" for i in range(59, 64)))
    print("  Block 0 - Lowercase 65-90: "
          + " ".join(f"{charmap0.get(i,'?')}" for i in range(65, 91)))
    print("  Block 0 - Special 91-95: "
          + " ".join(f"{charmap0.get(i,'?')}" for i in range(91, 96)))
    print("  Block 0 - Roman/symbols 96-111: "
          + " ".join(f"{charmap0.get(i,'?')}" for i in range(96, 112)))

    # Print block 0 kana summary
    print(f"  Block 0 - Kana 112-255: "
          f"{sum(1 for i in range(112,256) if i in charmap0)} chars mapped")

    # ---- Stat Kanji Positions ----
    print("\n=== STAT KANJI POSITIONS ===")
    print(f"  {'Kanji':<6} {'Block':>5} {'Row':>4} {'Col':>4} {'Cell':>5} {'Global':>7}")
    print(f"  {'-----':<6} {'-----':>5} {'---':>4} {'---':>4} {'----':>5} {'------':>7}")
    for kanji, (sb, row, col) in sorted(STAT_KANJI_POSITIONS.items(),
                                         key=lambda x: x[1][0] * 256 + x[1][1] * 16 + x[1][2]):
        cell = row * 16 + col
        glob = sb * 256 + cell
        # Verify against our kanji string
        kanji_str = kanji_strings[sb - 1] if 1 <= sb <= 3 else ""
        expected = kanji_str[cell] if cell < len(kanji_str) else "?"
        match = "OK" if expected == kanji else f"MISMATCH(got '{expected}')"
        print(f"  {kanji:<6} {sb:>5} {row:>4} {col:>4} {cell:>5} {glob:>7}  [{match}]")

    # ---- Composite image ----
    print("\n=== Creating Composite Image ===")
    composite = create_composite(grid_images, all_ink)
    comp_path = os.path.join(OUT_DIR, "r2100_composite.png")
    composite.save(comp_path)
    print(f"  Saved: {comp_path}")

    # ---- Summary and JSON output ----
    total = sum(sum(1 for d in dd if d > 0) for dd in all_ink)
    print(f"\n=== SUMMARY ===")
    print(f"  Total glyph cells across all 4 sub-blocks: {total}/1024")
    for i in range(4):
        occ = sum(1 for d in all_ink[i] if d > 0)
        print(f"  Sub-block {i}: {occ}/256 occupied")

    # Build full glyph map with character info for ALL blocks
    glyph_map = {
        "description": "R2100 chargen font atlas glyph map",
        "format": "4 sub-blocks of 256x256 PSMT4, 16x16 cells, 256 cells/block",
        "deswizzle": {"dbw_ct32": DBW_CT32, "bw_psmt4": BW_PSMT4},
        "stat_kanji": {k: {"sub_block": v[0], "row": v[1], "col": v[2],
                           "cell": v[1]*16+v[2], "global": v[0]*256+v[1]*16+v[2]}
                       for k, v in STAT_KANJI_POSITIONS.items()},
        "sub_blocks": [],
    }

    for sb_idx in range(4):
        sb_data = {
            "index": sb_idx,
            "total_occupied": sum(1 for d in all_ink[sb_idx] if d > 0),
            "cells": [],
        }
        cm = charmap_all[sb_idx]
        for r in range(ROWS):
            for c in range(COLS):
                idx = r * COLS + c
                ink = all_ink[sb_idx][idx]
                cell_info = {
                    "cell_index": idx,
                    "global_index": sb_idx * 256 + idx,
                    "row": r,
                    "col": c,
                    "ink_pixels": ink,
                    "has_glyph": ink > 0,
                }
                if idx in cm:
                    cell_info["character"] = cm[idx]
                    if sb_idx == 0 and idx < 59:
                        cell_info["ascii_code"] = idx + 0x20
                sb_data["cells"].append(cell_info)
        glyph_map["sub_blocks"].append(sb_data)

    json_path = os.path.join(OUT_DIR, "r2100_glyph_map.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(glyph_map, f, indent=2, ensure_ascii=False)
    print(f"  Saved glyph map: {json_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
