import sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

def analyze(path, label, ytop=0):
    im=np.asarray(Image.open(path).convert('L')).astype(np.float32)
    H,W=im.shape
    print(f"=== {label} {W}x{H} ===")
    # Row-wise brightness in the lower portion (dialogue box). Text glyphs are bright on dark box.
    # Compute per-row mean of bright pixels (>threshold)
    rowscore=[]
    for y in range(H):
        row=im[y]
        bright=(row>150).sum()
        rowscore.append(bright)
    rowscore=np.array(rowscore)
    # Find peaks: rows with many bright px = glyph rows
    for y in range(H):
        if rowscore[y]>8:
            bar='#'*min(60,rowscore[y]//3)
            print(f"{y:3d} {rowscore[y]:4d} {bar}")
analyze('build/recon_portrait4/extract/nshadymanand4linesinsteadof3__shot.png','nshadyman')
