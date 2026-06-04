#!/usr/bin/env python3
"""
Render individual character extractions from R2138 sub25 for final identification.
Save zoomed PNGs of each identified character region.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw")
DUMP_DIR = os.path.join(BASE, "dumps")

SUB_OFFSET = 0x15C4D0
HEADER_SIZE = 0x6E0
PIXEL_OFFSET = SUB_OFFSET + HEADER_SIZE
PIXEL_SIZE = 32768
TEX_W, TEX_H = 256, 256
DBW_CT32 = 128

data = open(RAW_PATH, 'rb').read()
pixel_data = data[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE]
pixels = deswizzle_psmt4(pixel_data, TEX_W, TEX_H, dbw_ct32=DBW_CT32)

def extract_region(x1, y1, x2, y2, zoom=10, name=""):
    w, h = x2 - x1, y2 - y1
    img = Image.new('L', (w * zoom, h * zoom))
    for dy in range(h):
        for dx in range(w):
            v = pixels[(y1+dy) * TEX_W + (x1+dx)] * 17
            for zy in range(zoom):
                for zx in range(zoom):
                    img.putpixel((dx*zoom+zx, dy*zoom+zy), v)
    path = os.path.join(DUMP_DIR, name)
    img.save(path)
    print(f"  Saved: {name}")
    return path

# Region 4: split into meaningful portions based on density analysis
# The big shape x4-65 is one continuous mass with internal structure
# After x65, density drops sharply (x66-71 are very low)
# Then x72-122 is another mass

# Region 4 analysis: looking at the thresholded patterns:
# LEFT x4-65:
#   Top (y190): narrow triangle peak
#   Middle: expands with curving strokes
#   Bottom (y208): flat wide base spanning full width
#   This matches a レベル (re-be-ru) katakana rendering as a single styled word
#   - The expanding curve on the left matches レ (re)
#   - The middle structure with internal lines matches ベ (be)
#   - The right vertical strokes match ル (ru)
# After gap:
# RIGHT x72-122 has TWO peaks visible in density:
#   Peak 1: x75-89 = one shape
#   Peak 2: x93-105 = another shape
#   Plus small appendage x109-120
# This matches アップ!!
#   - ア (a): x72-89
#   - ッ (small tsu): x93-105 (smaller)
#   - プ (pu): x105-120
#   Plus !! marks

print("Rendering character extractions...")

# Full regions at 8x
extract_region(4, 176, 122, 217, 8, "r2138_sub25_region4_8x.png")
extract_region(144, 176, 188, 217, 8, "r2138_sub25_region5_8x.png")
extract_region(5, 224, 121, 254, 8, "r2138_sub25_region6_8x.png")
extract_region(0, 128, 256, 170, 8, "r2138_sub25_region3_8x.png")

# Individual character extractions for regions 4, 5, 6
# Region 4 - left portion (レベル)
extract_region(4, 188, 65, 212, 10, "r2138_sub25_r4_reberu_10x.png")
# Region 4 - right portion (アップ!!)
extract_region(66, 185, 122, 215, 10, "r2138_sub25_r4_appu_10x.png")

# Region 5 upper - 3 small chars
extract_region(146, 176, 158, 192, 12, "r2138_sub25_r5u_char1_12x.png")
extract_region(159, 176, 172, 192, 12, "r2138_sub25_r5u_char2_12x.png")
extract_region(174, 176, 186, 192, 12, "r2138_sub25_r5u_char3_12x.png")

# Region 5 lower - 2 chars
extract_region(145, 198, 167, 217, 12, "r2138_sub25_r5l_char1_12x.png")
extract_region(174, 198, 188, 217, 12, "r2138_sub25_r5l_char2_12x.png")

# Region 6 - sections
extract_region(5, 226, 59, 249, 10, "r2138_sub25_r6_left_10x.png")
extract_region(59, 226, 107, 249, 10, "r2138_sub25_r6_mid_10x.png")
extract_region(107, 226, 121, 253, 10, "r2138_sub25_r6_right_10x.png")

# Region 3 inverted chars
extract_region(35, 153, 67, 166, 12, "r2138_sub25_r3_seg0_12x.png")
extract_region(130, 153, 206, 166, 8, "r2138_sub25_r3_seg1_8x.png")
extract_region(213, 153, 232, 166, 12, "r2138_sub25_r3_triangle_12x.png")

print("\nAll extractions complete.")
print()
print("=" * 70)
print("CHARACTER IDENTIFICATION SUMMARY")
print("=" * 70)
print()
print("REGION 4 (x4-122, y176-217): Level Up notification text")
print("  LEFT half (x4-65): レベル (reberu = Level)")
print("    - Katakana characters rendered as one flowing word")
print("    - レ: left expanding curve (x4-22)")
print("    - ベ: middle strokes with horizontal lines (x22-48)")
print("    - ル: right double vertical strokes (x48-65)")
print("  RIGHT half (x66-122): アップ!! (appu!! = Up!!)")
print("    - Gap at x66-71 separates the two words")
print("    - アッ: katakana a+small tsu (x72-105)")
print("    - プ: katakana pu (x105-118)")
print("    - !!: exclamation marks (x116-120)")
print()
print("  COMBINED: レベルアップ!! = LEVEL UP!!")
print()
print("REGION 5 (x144-188, y176-217): Two stacked labels")
print("  UPPER (y176-192): 3 small characters")
print("    Char 1 (x146-158): 次 (tsugi = next)")
print("    Char 2 (x159-172): の (no = possessive particle)")
print("    Char 3 (x174-186): - hard to tell, could be レ or similar")
print("    Candidates: 次のレベル (next level), 次の... (next ...)")
print("  LOWER (y198-217): 2 characters")
print("    Char 1 (x145-167): 全 (zen) - wide triangle with base = all/total")
print("    Char 2 (x174-188): 員 (in) - complex box character = member")
print("    COMBINED: 全員 (zen'in = everyone/all members)")
print()
print("REGION 6 (x5-121, y224-254): Second large text line")
print("  LEFT (x5-59): Multiple katakana characters")
print("    - Expanding curve + internal strokes pattern")
print("    - Similar rendering style to Region 4")
print("  MID (x59-107): More katakana + stroke patterns")
print("    - Contains vertical line (x61-63) = tall stroke")
print("    - Followed by more complex shapes")
print("  RIGHT (x109-121): Two parallel vertical strokes")
print("    - Two columns of dots/lines separated by gap")
print("    - These are !! (double exclamation marks)")
print("    - Each has a dot below (y246-248) confirming !!")
print()
print("  Region 6 full text analysis:")
print("  Looking at the LEFT section character by character:")
print("    x5-22: レ-like expanding curve")
print("    x22-33: ベ-like pattern (but less clear)")
print("    x33-59: ル-like + more strokes")
print("  The density dip at x48 and x59 suggests character boundaries")
print()
print("REGION 3 (x0-256, y128-170): Banner/title bar")
print("  Segment 0 (x35-67): 2 inverted kanji on gradient background")
print("    全員 (zen'in = everyone) - matches R5 lower")
print("  Segment 1 (x130-206): Multiple inverted kanji")
print("    ~5 characters, each ~14-16px wide")
print("  Segment 2 (x213-232): Triangle/arrow decorative element")
