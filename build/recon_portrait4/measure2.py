import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np

def analyze(name):
    im=Image.open(f'build/recon_portrait4/extract/{name}__shot.png').convert('RGB')
    a=np.array(im).astype(np.int32)
    h,w,_=a.shape
    # text is light gray/white on dark. brightness
    lum=a.mean(axis=2)
    # bottom half where dialogue box is
    # find the box: dialog box has a distinct frame. Look at rows 380-470
    print(f"=== {name} ({w}x{h}) ===")
    # per-row count of bright pixels (text)
    bright=lum>140
    rowsum=bright.sum(axis=1)
    # find text rows in bottom region
    for y in range(380,h):
        if rowsum[y]>15:
            pass
    # Identify columns with text in the dialogue area (y 400-470)
    region=bright[395:475,:]
    colsum=region.sum(axis=0)
    cols=np.where(colsum>2)[0]
    if len(cols):
        print(f"  text col range x=[{cols.min()},{cols.max()}] width={cols.max()-cols.min()}")
    # box frame: look for the horizontal bright frame lines
    rows=np.where(rowsum[380:]>40)[0]+380
    if len(rows):
        print(f"  bright rows y=[{rows.min()},{rows.max()}]")

for n in ['ladyknightnoportrait','Tooearlylinewrap','nshadymanand4linesinsteadof3','nosister']:
    analyze(n)
