import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
BASE = "C:/programmieren/wizardrytranslation"
sys.path.insert(0, os.path.join(BASE, "tools"))
from strip_patcher import load_font

cfg = json.load(open(os.path.join(BASE,"data/strip_labels/r2880_prologue.json"), encoding="utf-8"))
left_pad = cfg["layout"]["left_pad"]
size = cfg["layout"]["font_size"]
font = load_font(size, bold=True)

print(f"font_size={size} bold left_pad={left_pad}")
print(f"{'i':>2} {'win':>12} {'winw':>5} {'cap':>4} {'ink':>4} {'marg':>5} {'flag':>8} seg")
rows=[]
for i, ln in enumerate(cfg["lines"]):
    for k,((x0,x1),text) in enumerate(zip(ln["windows"], ln["segs"])):
        win_w = x1-x0
        cap = win_w - left_pad
        bbox = font.getbbox(text)
        tw = bbox[2]-bbox[0]
        marg = cap - tw
        center_gap = (win_w - tw)//2
        flag = ""
        if marg < 4: flag = "TIGHT"
        if marg < 0: flag = "OVERFLOW"
        rows.append((marg, i, k, x0, x1, win_w, cap, tw, center_gap, text, flag))
        print(f"{i:>2} [{x0:>3},{x1:>3}] {win_w:>5} {cap:>4} {tw:>4} {marg:>5} {flag:>8} k{k} '{text}' (ctr-gap {center_gap})")

print("\n--- sorted by margin (most suspect first) ---")
for r in sorted(rows)[:8]:
    print(f"margin={r[0]:>4} i={r[1]} win[{r[3]},{r[4]}] ink={r[7]} '{r[9]}' {r[10]}")

print("\n--- em-dash glyph check (i8 'beastmen to attack ') ---")
for ch in ["—","-","–"]:
    bb = font.getbbox(ch)
    print(f"  {repr(ch)} bbox={bb} width={bb[2]-bb[0] if bb else 0}")
from PIL import Image, ImageDraw
img = Image.new("L",(40,30),0); d=ImageDraw.Draw(img); d.text((2,2),"—",fill=255,font=font)
nz = sum(1 for p in img.getdata() if p>0)
print(f"  em-dash rendered non-zero pixels: {nz} (0 = tofu/missing)")
