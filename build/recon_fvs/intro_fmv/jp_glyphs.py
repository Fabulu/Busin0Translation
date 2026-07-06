import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
cfg=json.load(open("data/strip_labels/r2880_prologue.json",encoding="utf-8"))
# JP char counts per line vs measured ink width -> px/glyph
inkruns={ # from page_ink.py: total ink width per line
0:378,1:301,2:221,3:452,4:423,5:198,6:211,7:294,8:223,9:283,
10:318,11:294,12:191,13:318,14:462,15:295,16:478,17:164}
for i,ln in enumerate(cfg["lines"]):
    jp=ln["jp"]
    # count visible chars (drop spaces incl. ideographic space U+3000)
    chars=[c for c in jp if c not in (' ','　')]
    n=len(chars)
    w=inkruns[i]
    print(f"line{i:2} JPchars={n:2} inkW={w:3}px  px/glyph={w/n:5.1f}  jp='{jp}'")
