import json, struct, os
from PIL import ImageFont

RES="build/packdata_resources"
AR="C:/Windows/Fonts/arialbd.ttf"
TI="C:/Windows/Fonts/timesbd.ttf"
_fc={}
def F(p,s):
    k=(p,s)
    if k not in _fc:_fc[k]=ImageFont.truetype(p,s)
    return _fc[k]
def W(t,p,s,stroke=0):
    if not t:return 0
    b=F(p,s).getbbox(t,stroke_width=stroke)
    return (b[2]-b[0]) if b else 0

def parse_rects(name,off):
    with open(os.path.join(RES,name),"rb") as f:data=f.read()
    m,c=struct.unpack_from(">2I",data,off);assert m==5
    return {i:struct.unpack_from(">5I",data,off+8+i*20)[2] for i in range(c)}

RT={}
for nm,(fn,off) in {
 "R1359":("1359_type02.raw",34656),"R1367":("1367_type02.raw",35632),
 "R1054":("1054_type02.raw",34656),"R1360":("1360_type02.raw",34656),
 "R1361":("1361_type02.raw",34656),"R1362":("1362_type02.raw",34656),
 "R1363":("1363_type02.raw",38560),"R1364":("1364_type04.raw",35456),
 "R1365":("1365_type02.raw",35712)}.items():
    RT[nm]=parse_rects(fn,off)

def cls(r,b):
    if r<=b:return "fits"
    if r<=b+4:return "near-miss"
    return "overflow"

# measurement models -> returns rendered px (at final shrunk size) + size
def m_r2124(t,avail):
    s=13
    while W(t,AR,s,1)>avail and s>9:s-=1
    return W(t,AR,s,1),s
def m_render_label(t,w,p=AR,start=13,floor=7):
    s=start
    while W(t,p,s)>w-2 and s>floor:s-=1
    return W(t,p,s),s
def m_fit_then_render(t,w,start=13):
    s=start
    while W(t,AR,s)>w-4 and s>9:s-=1
    while W(t,AR,s)>w-2 and s>7:s-=1
    return W(t,AR,s),s
def m_facility(t,w,start=12):
    s=start
    while W(t,AR,s)>w-2 and s>9:s-=1
    return W(t,AR,s),s
def m_r1365(t,w,start):
    s=start
    while W(t,TI,s)>w-2 and s>9:s-=1
    return W(t,TI,s),s

res=[]
def add(file,name,eng,rect_w,rendered,budget,size,basis,proposed="",prop_px=0):
    res.append(dict(file=file,name=name,english=eng,rect_w=rect_w,rendered_px=rendered,
        budget_px=budget,status=cls(rendered,budget),size=size,canonical_basis=basis,
        proposed=proposed,proposed_px=prop_px))

# ---------- R2124 (budget = rect.w - x_offset, stroke=1, floor 9 hard) ----------
r2124=[("L0_inn","Adventurer's Inn",128,2),("L1_temple","Church of Salem",128,2),
("L2_alchguild","Alchemy Guild",128,2),("L3_shop","Vigger Shop",128,2),
("L4_tavern","Bar Luna Light",128,2),("L5_advguild","Adventurer's Guild",128,2),
("L6_karman","Karman's Labyrinth",128,2),("L7_tower","Tower of Tebayd",128,2),
("R0_townhall","Town Hall Plaza",128,16),("R1_faubourg","Faubourg District",128,16),
("R2_porola","Porola District",128,16),("R3_vare","Vare District",128,16),
("R4_castle","Duhan Castle",128,16)]
for nm,eng,w,xo in r2124:
    avail=w-xo
    rd,sz=m_r2124(eng,avail)
    prop="";pp=0
    if rd>avail:
        # propose alternatives consistent with glossary/dialogue
        cand={"Church of Salem":"Salem Church","Adventurer's Guild":"Adventurers Guild",
              "Karman's Labyrinth":"Karman Labyrinth","Faubourg District":"Faubourg Dist."}.get(eng)
        if cand:
            pp,_=m_r2124(cand,avail);prop=cand
    add("data/strip_labels/r2124_labels.json",nm,eng,w,rd,avail,sz,"glossary.locations / chunk dialogue",prop,pp)

print(json.dumps(res,indent=0))
