import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
img=Image.open(sys.argv[1]).convert('RGB')
W,H=img.size; px=img.load()
# Find the box frame: the ornate metallic frame is the brightest sustained vertical
# structure. Look for the box's inner text area. The white italic text is near-white.
# 1) Locate text rows: rows with many near-white pixels in lower half.
def whitecount(y):
    return sum(1 for x in range(W) if min(px[x,y])>150 and sum(px[x,y])>520)
rows=[(y,whitecount(y)) for y in range(H//2,H)]
textrows=[y for y,c in rows if c>8]
if textrows:
    print(f"text rows y={min(textrows)}..{max(textrows)}")
# 2) For those rows, find min/max x of near-white text pixels
xs=[]
for y in textrows:
    for x in range(W):
        if min(px[x,y])>150 and sum(px[x,y])>520:
            xs.append(x)
if xs:
    print(f"TEXT x extent: {min(xs)} .. {max(xs)}  (width {max(xs)-min(xs)})")
# 3) Find the box frame edges: scan for the bright frame border (the metallic frame
# is bright but not white). Look at a row just above text for the frame top, and
# find left/right frame columns by the bright vertical bars.
# The frame: find columns where, over the box y-range, there's a bright run.
ytop=min(textrows)-20 if textrows else H-120
ybot=max(textrows)+20 if textrows else H-10
def colmaxbright(x):
    return max(sum(px[x,y])//3 for y in range(max(0,ytop),min(H,ybot)))
# frame columns: brightness > 120 sustained
frameL=None;frameR=None
for x in range(W):
    if colmaxbright(x)>110:
        if frameL is None: frameL=x
        frameR=x
print(f"box bright extent (frame incl): {frameL}..{frameR}")
