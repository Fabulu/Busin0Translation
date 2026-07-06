from PIL import Image
import numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

for name in ['shady4','BarkeepOverflow']:
    im=Image.open(f'build/recon_tri2/{name}__shot.png').convert('RGB')
    a=np.array(im).astype(np.int32)
    H,W,_=a.shape
    lum=a.mean(axis=2)
    # The dialogue box is in the bottom ~third. Text glyphs are bright on dark box.
    # Find the box: bottom region y in [330,470]. Text starts left.
    # Build an ink mask: pixel brighter than local box background.
    # Use a threshold relative to row: glyph pixels are notably brighter.
    # Focus on the text area columns. Print column-band luminance to find box.
    # First, per-row count of 'bright' pixels (lum>110) in x range covering text.
    print(f'=== {name} ===')
    # estimate box top by scanning where a horizontal dark band begins in bottom third
    # Just compute bright-pixel count per row over full width in bottom region
    thr=110
    for y in range(330,475):
        cnt=int((lum[y]>thr).sum())
        bar='#'*min(cnt,80)
        print(f'{y:3d} {cnt:3d} {bar}')
    print()
