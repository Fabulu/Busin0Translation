$script = @'
import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw

FONT_FILE = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin'
EXE_FILE = r'C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78'
OUTDIR = r'C:/Programmieren/wizardrytranslation/dumps/font_renders/pages'
os.makedirs(OUTDIR, exist_ok=True)

exe = open(EXE_FILE, 'rb').read()

# Analyze metric+row+col as a combined coordinate system
# The per-glyph struct is 28 bytes at 0x3C0E78
# Byte 9 = metric, byte 17 = atlas_row, byte 18 = atlas_col
BASE = 0x3C0E78
f240 = struct.pack('<ff', 240.0, 240.0)
n = 0
while exe[BASE+n*28:BASE+n*28+8] == f240 and n < 2000:
    n += 1

print(f'Total 240.0-group entries: {n}')
print()

# Dump ALL bytes of struct to understand all fields
print('=== Full struct dump for first 30 glyphs ===')
for i in range(min(30, n)):
    o = BASE + i * 28
    raw = exe[o:o+28]
    # floats at 0:8
    f1, f2 = struct.unpack_from('<ff', raw, 0)
    # All remaining bytes
    rest = raw[8:]
    print(f'glyph[{i:3d}] f={f1:.0f},{f2:.0f} bytes[8:28]={rest.hex(" ")}')

print()
print('=== Analyzing metric as bit field ===')
# Maybe metric encodes x,y position within a page/block
# row,col select the 128x128 page (or 32x16 block?)
for i in range(min(n, 105)):
    o = BASE + i * 28
    metric = exe[o+9]
    row = exe[o+17]
    col = exe[o+18]
    # Decode metric bits
    b7 = (metric >> 7) & 1
    b6 = (metric >> 6) & 1
    b5 = (metric >> 5) & 1
    b4 = (metric >> 4) & 1
    b3 = (metric >> 3) & 1
    b2 = (metric >> 2) & 1
    b1 = (metric >> 1) & 1
    b0 = metric & 1
    # Try different split interpretations
    hi4 = (metric >> 4) & 0xF  # upper nibble
    lo4 = metric & 0xF  # lower nibble
    if i < 105:
        print(f'  glyph[{i:3d}] metric={metric:3d} 0x{metric:02X} bin={metric:08b} hi={hi4:2d} lo={lo4:2d} row={row} col={col}')

# ASCII table cross-ref
print()
print('=== ASCII glyph: metric interpretation ===')
T = 0x3C0870
for j in range(84):
    o2 = T + j * 2
    glyph_idx = struct.unpack_from('<H', exe, o2)[0]
    ac = 0x20 + j
    ch = chr(ac) if 32 <= ac < 127 else '?'
    if glyph_idx < n:
        o = BASE + glyph_idx * 28
        metric = exe[o+9]
        row = exe[o+17]
        col = exe[o+18]
        hi4 = (metric >> 4) & 0xF
        lo4 = metric & 0xF
        # Compute absolute pixel position if metric encodes (x,y) within page
        # Hypothesis: col selects column-block (32px wide), row selects page row
        # metric encodes position within that region
        print(f'  ASCII 0x{ac:02X} {ch} -> glyph {glyph_idx:3d} metric=0x{metric:02X}({metric:3d}) row={row} col={col} hi={hi4:2d} lo={lo4:2d}')

# Now try interpreting row/col differently
# What if row and col are not page indices but direct pixel coordinates?
# row 0-6 with col 0-3 gives only 28 positions
# But we have 105 glyphs, so metric must sub-index within each row/col
# With 8 glyphs at row=1,col=0 and metric vals [14,44,74,104,134,164,194,224]
# Differences: 30, 30, 30, 30, 30, 30, 30 -- EXACTLY 30 apart!
print()
print('=== Metric spacing analysis per page ===')
from collections import Counter
page_glyphs = {}
for i in range(n):
    o = BASE + i * 28
    metric = exe[o+9]
    row = exe[o+17]
    col = exe[o+18]
    key = (row, col)
    if key not in page_glyphs:
        page_glyphs[key] = []
    page_glyphs[key].append((metric, i))

for key in sorted(page_glyphs.keys()):
    vals = sorted(page_glyphs[key])
    metrics = [v[0] for v in vals]
    if len(metrics) > 1:
        diffs = [metrics[i+1] - metrics[i] for i in range(len(metrics)-1)]
        print(f'  row={key[0]} col={key[1]}: metrics={metrics} diffs={diffs}')
    else:
        print(f'  row={key[0]} col={key[1]}: metrics={metrics}')

# Now check: if metric is a pixel coordinate within a texture region,
# and each row/col defines a region, what is the mapping?
# With row 0-6 (7 levels) and col 0-3 (4 levels) plus spacing of 30 or 15:
# This looks like GS texture coordinates in 1/16th pixel units
# or perhaps the metric IS the glyph Y position within a 256-pixel page

print()
print('=== Hypothesis: metric = Y pixel position within texture page ===')
print('Row/col define which 256x256 page, metric = Y coord within page')
print()
print('If texture is 256x512 (as stored), possible interpretations:')
print('  - 4 columns (col 0-3) x many rows: col*64=x?, metric=y?')
print('  - Or metric is an index into a glyph table within that page')

# Most telling: row=1,col=0 has metrics [14,44,74,104,134,164,194,224]
# These are spaced 30 apart: 14, 14+30=44, 44+30=74, etc.
# If glyph height = 16px and spacing includes padding, maybe 30 = 2*16 - 2?
# Or if metric is in some scaled unit...

# Let me check: the font descriptors had tex_param_b = 16, 32, 48, 64
# These might be y-offsets for each row group in the descriptor table
# And metric might be the sub-position within each group

# Actually, look at the per-glyph struct more carefully
# The struct has byte 17=row and byte 18=col
# Let me re-examine what other bytes contain
print()
print('=== Full byte analysis of per-glyph structs ===')
print('Examining all non-zero bytes across all 105 entries')
byte_vals = {}
for b in range(28):
    vals = set()
    for i in range(n):
        o = BASE + i * 28
        vals.add(exe[o+b])
    if len(vals) > 1 or (len(vals) == 1 and 0 not in vals):
        byte_vals[b] = sorted(vals)
        print(f'  byte[{b:2d}]: {len(vals)} unique values: {sorted(vals)[:20]}')

print()
print('Done!')
'@
Set-Content -Path 'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon33-atlas-ocr/atlas_struct_analyze.py' -Value $script -Encoding UTF8
Write-Host "Script written OK"
