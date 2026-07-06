import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np
# Use ladyknight: "break the spirit" is the widest line (16 chars, fills box)
im=Image.open('build/recon_portrait4/extract/ladyknightnoportrait__shot.png').convert('RGB')
a=np.array(im).astype(np.int32)
lum=a.mean(axis=2)
# In the upscaled crop the box started ~y=370. Find the "break the spirit" row.
# Original coords: examine rows 400-470 for bright text columns
bright=lum>150
# scan each candidate text row band, find leftmost/rightmost bright col excluding frame
# The frame ornaments are at far left (~x<60) and far right (~x>580). Text between.
# Find rows with substantial text
for y0,y1,label in [(405,425,'line1'),(425,445,'line2'),(445,465,'line3')]:
    band=bright[y0:y1, 60:585]
    cols=np.where(band.sum(axis=0)>1)[0]
    if len(cols):
        print(f"{label} y[{y0}:{y1}]: text x=[{cols.min()+60},{cols.max()+60}] span={cols.max()-cols.min()}")
# Also find box frame inner edges: look at a row, the bright vertical frame
# Find leftmost text start across all lines = left margin
