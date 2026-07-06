import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
img=Image.open(sys.argv[1]).convert('RGB')
W,H=img.size; px=img.load()
# Dialogue body is in y ~ 395..473 (below the name line ~363-390). Avoid portrait (y<360).
y0,y1=395,474
xs=[]
for y in range(y0,y1):
    for x in range(W):
        r,g,b=px[x,y]
        if min(r,g,b)>140 and r+g+b>500:
            xs.append((x,y))
if xs:
    X=[x for x,y in xs]
    print(f"{sys.argv[1].split(chr(92))[-2]}: text body x {min(X)}..{max(X)} width {max(X)-min(X)}, rows {min(y for x,y in xs)}..{max(y for x,y in xs)}")
    # per-row right edge to find the widest line
    from collections import defaultdict
    rowmax=defaultdict(int); rowmin=defaultdict(lambda:9999)
    for x,y in xs:
        rowmax[y]=max(rowmax[y],x); rowmin[y]=min(rowmin[y],x)
    print("  widest line right-edge:", max(rowmax.values()))
