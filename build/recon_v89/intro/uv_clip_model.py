import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np

# Per-line UV caps (from committed HEAD r2880_prologue.json) and left_x origin
caps=[378,301,221,452,423,198,211,294,223,283,318,294,191,318,462,295,478,164]
left_x=4
lines=["Long ago, for thirty long years,","a war plunged the Kingdom of Duhan",
"into blood and terror.","The devastating war that cut","the kingdom's people to two-thirds",
"would be remembered as the Battle of Banquo.","Possessed by a death spirit,",
"the San-Goth king led his beastmen","forth to attack —","that was how it all began,",
"but war soon engulfed all of Venoa.","Had one hero not appeared,","the Kingdom of Duhan",
"would have vanished from the earth.","He was Ortrud, later known as the Holy King.",
"He defeated San-Goth and restored","peace and hope to the Kingdom of Duhan.","Twenty years passed..."]

# measure centered text x-extent per line in v89 decoded texture
img=np.array(Image.open('build/recon_v89/intro/r2880s7_v89.png').convert('L'))
line_tops=[1,25,49,73,97,121,145,169,194,218,241,265,290,313,337,361,385,409]
print("MODEL: movie samples each line through UV window [left_x, left_x+cap].")
print("centered text outside that window is CLIPPED in-engine.\n")
print(f"{'i':>2} {'cap':>4} {'win_R':>5} {'cen_L':>5} {'cen_R':>5} {'clip?':>6}  text")
for i,top in enumerate(line_tops):
    band=img[top:top+23,:]
    dark=np.where(band.min(axis=0)<128)[0]
    if not len(dark):
        print(f"{i:2} {caps[i]:4} (empty)"); continue
    cl,cr=dark.min(),dark.max()
    win_r=left_x+caps[i]
    clipped = cr>win_r
    # fraction of width visible
    vis = max(0,min(cr,win_r)-cl)
    tot = cr-cl
    frac = vis/tot if tot else 1
    flag = f"CLIP {frac*100:.0f}%" if clipped else "ok"
    print(f"{i:2} {caps[i]:4} {win_r:5} {cl:5} {cr:5} {flag:>6}  {lines[i][:40]}")
