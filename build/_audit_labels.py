import json, struct, os
from PIL import ImageFont

RES = "build/packdata_resources"
ARIALBD = "C:/Windows/Fonts/arialbd.ttf"
TIMESBD = "C:/Windows/Fonts/timesbd.ttf"

_fc = {}
def font(path, size):
    k=(path,size)
    if k not in _fc: _fc[k]=ImageFont.truetype(path, size)
    return _fc[k]

def width(text, path, size, stroke=0):
    if not text: return 0
    bbox = font(path,size).getbbox(text, stroke_width=stroke)
    return (bbox[2]-bbox[0]) if bbox else 0

# ---- measurement replicas ----
def measure_r2124(text, avail):
    # start 13, floor 9, stroke 1, measure stroked width
    size=13
    while True:
        tw = width(text, ARIALBD, size, stroke=1)
        if tw <= avail or size <= 9: break
        size -= 1
    return width(text, ARIALBD, size, stroke=1), size

def measure_render_label(text, w, path=ARIALBD, start=13, floor=7):
    # strip_patcher.render_label shrink: while bbox > w-2 and size>7
    size=start
    while width(text,path,size) > w-2 and size>floor:
        size -= 1
    return width(text,path,size), size

def measure_fitfont_then_render(text, w, start=13):
    # fit_font: shrink to floor 9 against w-4, then render_label re-shrinks vs w-2 floor 7
    size=start
    while width(text,ARIALBD,size) > w-4 and size>9:
        size -= 1
    # render_label further
    while width(text,ARIALBD,size) > w-2 and size>7:
        size -= 1
    return width(text,ARIALBD,size), size

def measure_facility(text, w, start=12):
    # floor 9, budget w-2
    size=start
    while width(text,ARIALBD,size) > w-2 and size>9:
        size -= 1
    return width(text,ARIALBD,size), size

def measure_r1365(text, w, start):
    # serif, floor 9, budget w-2
    size=start
    while width(text,TIMESBD,size) > w-2 and size>9:
        size -= 1
    return width(text,TIMESBD,size), size

def classify(rendered, budget):
    if rendered <= budget: return "fits"
    if rendered <= budget+4: return "near-miss"
    return "overflow"

# ---- rect table parser ----
def parse_rects(data, off):
    magic,count = struct.unpack_from(">2I", data, off)
    assert magic==5, f"bad magic {magic} @ {off}"
    out={}
    for i in range(count):
        x,y,w,h,clut = struct.unpack_from(">5I", data, off+8+i*20)
        out[i]={"x":x,"y":y,"w":w,"h":h}
    return out

def load_res(name):
    with open(os.path.join(RES,name),"rb") as f: return f.read()

# load rect tables
rects = {}
rects["R1359"] = parse_rects(load_res("1359_type02.raw"), 34656)
rects["R1367"] = parse_rects(load_res("1367_type02.raw"), 35632)
rects["R1054"] = parse_rects(load_res("1054_type02.raw"), 34656)
rects["R1360"] = parse_rects(load_res("1360_type02.raw"), 34656)
rects["R1361"] = parse_rects(load_res("1361_type02.raw"), 34656)
rects["R1362"] = parse_rects(load_res("1362_type02.raw"), 34656)
rects["R1363"] = parse_rects(load_res("1363_type02.raw"), 38560)
rects["R1364"] = parse_rects(load_res("1364_type04.raw"), 35456)
rects["R1365"] = parse_rects(load_res("1365_type02.raw"), 35712)

import sys
def emit(rows):
    for r in rows:
        print(json.dumps(r))

results=[]

def add(file,name,english,rect_w,rendered,budget,proposed="",proposed_px=0,size=0):
    st=classify(rendered,budget)
    results.append({"file":file,"name":name,"english":english,"rect_w":rect_w,
        "rendered_px":rendered,"budget_px":budget,"status":st,
        "proposed":proposed,"proposed_px":proposed_px,"size":size})

# ===== R2124 =====
r2124 = json.load(open("data/strip_labels/r2124_labels.json"))
# the file structure: find labels list
def find_labels(obj):
    if isinstance(obj,dict):
        if "labels" in obj and isinstance(obj["labels"],list): return obj["labels"]
        for v in obj.values():
            r=find_labels(v)
            if r: return r
    return None
# Use the provided list directly via input json embedded? We'll re-read from file.
print("R2124_FILE_KEYS", list(r2124.keys()) if isinstance(r2124,dict) else "list")
