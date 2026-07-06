import sys,os
sys.path.insert(0,"C:/programmieren/wizardrytranslation/tools")
from strip_patcher import load_font
sys.stdout.reconfigure(encoding='utf-8')
# For the 3 split lines, find where the current English text crosses the dead zone.
splits={
 0:[(0,72),(96,384)],
 3:[(0,144),(168,456)],
 4:[(0,192),(216,336),(336,432)],
 14:[(0,216),(240,384),(384,464)],
 16:[(0,192),(216,504)],
}
import json
cfg=json.load(open("data/strip_labels/r2880_prologue.json",encoding="utf-8"))
left_x=cfg["layout"]["left_x"]
for i,wins in splits.items():
    en=cfg["lines"][i]["en"]
    font=load_font(18,bold=True)
    # cumulative char x positions (left-aligned from left_x)
    print(f"\nline{i} EN='{en}'  windows={wins}  deadzones={[(wins[k][1],wins[k+1][0]) for k in range(len(wins)-1) if wins[k+1][0]>wins[k][1]]}")
    x=left_x
    prev=0
    crossing=[]
    for ci,ch in enumerate(en):
        bb=font.getbbox(en[:ci+1])
        w=bb[2]-bb[0]
        cx0=left_x; cx1=left_x+w
        # check if this char's right edge crosses a dead zone boundary
    # simpler: report the EN text x-extent vs first window right edge
    bb=font.getbbox(en); tot=bb[2]-bb[0]
    print(f"   EN total width={tot}px  first window right edge=uvX{wins[0][1]}  ->"
          f" {'TEXT SPILLS PAST WINDOW0 into deadzone' if tot>wins[0][1]-left_x else 'fits in window0'}")
