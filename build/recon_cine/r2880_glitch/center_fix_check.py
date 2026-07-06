import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
BASE="C:/programmieren/wizardrytranslation"
sys.path.insert(0, os.path.join(BASE,"tools"))
from strip_patcher import load_font
cfg=json.load(open(os.path.join(BASE,"data/strip_labels/r2880_prologue.json"),encoding="utf-8"))
font=load_font(18,bold=True)
left_pad=cfg["layout"]["left_pad"]
print("If we CENTER each seg in its window (ox = x0 + (winW - tw)//2):")
print(f"{'i':>2} {'win':>11} {'winW':>4} {'tw':>4} {'newOX':>5} {'inkR':>5} {'fits?':>6}")
for i,ln in enumerate(cfg["lines"]):
    for (x0,x1),text in zip(ln["windows"],ln["segs"]):
        winw=x1-x0; bb=font.getbbox(text); tw=bb[2]-bb[0]
        ox=x0+(winw-tw)//2
        inkR=ox+tw
        fits = x0<=ox and inkR<=x1
        print(f"{i:>2} [{x0:>3},{x1:>3}] {winw:>4} {tw:>4} {ox:>5} {inkR:>5} {'OK' if fits else 'OVERFLOW':>6}")
