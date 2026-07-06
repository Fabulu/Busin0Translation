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
    return "fits" if r<=b else ("near-miss" if r<=b+4 else "overflow")

# returns (rendered_px_at_final_size, final_size, hit_floor)
def m_r2124(t,avail):
    s=13
    while W(t,AR,s,1)>avail and s>9:s-=1
    w=W(t,AR,s,1);return w,s,(s==9 and w>avail)
def m_render_label(t,w,p=AR,start=13,floor=7):
    s=start
    while W(t,p,s)>w-2 and s>floor:s-=1
    ww=W(t,p,s);return ww,s,(s==floor and ww>w-2)
def m_fit_render(t,w,start=13):
    s=start
    while W(t,AR,s)>w-4 and s>9:s-=1
    while W(t,AR,s)>w-2 and s>7:s-=1
    ww=W(t,AR,s);return ww,s,(s==7 and ww>w-2)
def m_facility(t,w,start=12):
    s=start
    while W(t,AR,s)>w-2 and s>9:s-=1
    ww=W(t,AR,s);return ww,s,(s==9 and ww>w-2)
def m_r1365(t,w,start):
    s=start
    while W(t,TI,s)>w-2 and s>9:s-=1
    ww=W(t,TI,s);return ww,s,(s==9 and ww>w-2)

res=[]
def add(file,name,eng,rect_w,rd,bud,sz,floorhit,basis,prop="",pp=0,proc=None):
    # status: overflow only if at floor and still over budget OR rendered>budget;
    # near-miss if rendered within 4px of budget (tight) regardless of shrink
    if rd>bud:
        status="overflow"
    elif rd>bud-4:
        status="near-miss"
    else:
        status="fits"
    res.append(dict(file=file,name=name,english=eng,rect_w=rect_w,rendered_px=rd,
        budget_px=bud,status=status,final_size=sz,floor_hit=floorhit,
        canonical_basis=basis,proposed=prop,proposed_px=pp,proc=proc))

# ===== R2124 =====
F2124="data/strip_labels/r2124_labels.json"
r2124=[("L0_inn","Adventurer's Inn",128,2),("L1_temple","Church of Salem",128,2),
("L2_alchguild","Alchemy Guild",128,2),("L3_shop","Vigger Shop",128,2),
("L4_tavern","Bar Luna Light",128,2),("L5_advguild","Adventurer's Guild",128,2),
("L6_karman","Karman's Labyrinth",128,2),("L7_tower","Tower of Tebayd",128,2),
("R0_townhall","Town Hall Plaza",128,16),("R1_faubourg","Faubourg District",128,16),
("R2_porola","Porola District",128,16),("R3_vare","Vare District",128,16),
("R4_castle","Duhan Castle",128,16)]
PROP2124={"Church of Salem":"Salem Church","Karman's Labyrinth":"Karman Labyrinth",
 "Faubourg District":"Faubourg Dist."}
for nm,eng,w,xo in r2124:
    av=w-xo;rd,sz,fl=m_r2124(eng,av);prop="";pp=0
    if rd>av-4 and eng in PROP2124:
        prop=PROP2124[eng];pp,_,_=m_r2124(prop,av)
    add(F2124,nm,eng,w,rd,av,sz,fl,"glossary.locations + chunk_04 'Salem Church'",prop,pp,"r2124")

# ===== facility (budget w-2, floor 9, start = per-sheet 12) =====
FFAC="data/strip_labels/facility_labels.json"
fac=[("2141/temple/box[14,5]","Go Outside",100),("2141/temple/box[14,28]","Cure Poison",100),
("2141/temple/box[14,52]","Cure Paralysis",100),("2141/temple/box[14,77]","Cure Petrify",100),
("2141/temple/box[14,100]","Cure Fear",100),("2141/temple/box[14,124]","Raise Dead",100),
("2141/temple/box[14,148]","Restore Ashes",100),("2141/temple/box[14,172]","Exorcism",100),
("2141/temple/box[14,196]","Church of Salem",100),("2141/aux/box[156,174]","Donation",58),
("2141/aux/box[146,199]","Everyone",52),("2141/aux/box[134,231]","Everyone",50),
("2141/aux/box[188,231]","Everyone",52),("2144/inn/box[14,3]","Go Outside",100),
("2144/inn/box[14,28]","Stay",100),("2144/inn/box[14,51]","Adventurer's Inn",100),
("2144/aux/box[2,31]","Room Fee",64),("2150/sub0/box[8,3]","Go Outside",112),
("2150/sub0/box[8,27]","Vigger Shop",112),("2150/sub0/box[8,50]","Sell",112),
("2150/sub0/box[8,76]","Order",112),("2150/sub0/box[8,99]","Take Order",112),
("2150/sub0/box[8,123]","Check Orders",112),("2150/sub0/box[8,148]","Deliver",112),
("2150/sub0/box[8,171]","Identify",112),("2150/sub0/box[8,196]","Uncurse",112),
("2150/sub0/box[136,3]","Manage Shop",112),("2150/sub0/box[136,27]","Shop Info",112),
("2150/sub0/box[136,51]","Storage",112),("2150/sub0/box[136,75]","Manage Storage",112),
("2150/sub0/box[136,99]","Store Items",112),("2150/sub0/box[136,123]","Redecorate",112),
("2150/sub0/box[136,148]","Part-time Job",112),("2150/sub0/box[136,171]","Sales",112),
("2150/s1/box[0,117]","Wages",40),("2150/s1/box[78,117]","Uncurse Fee",84),
("2150/s1/box[157,117]","Identify Fee",84),("2150/s1/box[0,144]","Sell Price",84),
("2150/s1/box[0,169]","Shop Level",84),("2150/s1/box[78,169]","Fame",56),
("2150/s1/box[134,169]","Align",42),("2150/s1/box[0,190]","Title",64),
("2150/s1/box[54,190]","Sales",66),("2150/s1/box[128,190]","Branch",38),
("2150/s1/box[167,190]","Cost",38),("2150/s1/box[0,216]","Buy Price",84),
("2150/s1/box[88,216]","Room Fee",84),("2150/s2/box[12,3]","Shop Level",102),
("2150/s2/box[12,31]","Fame",80),("2150/s2/box[12,55]","Align",74),
("2150/s2/box[12,79]","Title",80),("2150/s2/box[12,102]","Sales",92),
("2150/s2/box[12,151]","Branch",64),("2150/s3/box[12,22]","Survey Skill",100),
("2150/s3/box[12,46]","Survival Rate",80),("2150/s3/box[12,70]","Trust",90),
("2150/s3/box[8,142]","Survey Skill",106),("2150/s3/box[8,156]","Survival Rate",70),
("2150/s3/box[8,182]","Trust",80),("2153/sub0/box[14,3]","Go Outside",100),
("2153/sub0/box[14,28]","Branch",100),("2153/sub0/box[14,52]","Buy",100),
("2153/sub0/box[14,76]","Sell",100),("2153/sub0/box[14,101]","Delivery",100),
("2153/sub0/box[14,124]","Events",100),("2153/sub0/box[14,148]","Rest Area",100)]
PROPFAC={}  # fill after seeing overflows
for nm,eng,w in fac:
    rd,sz,fl=m_facility(eng,w)
    add(FFAC,nm,eng,w,rd,w-2,sz,fl,"facility menu",PROPFAC.get(eng,""),0,"facility")

# ===== camp R1359/R1367 (fit_render budget w-4 pick, w-2 render, floor 9->7) =====
FCAMP="data/strip_labels/camp_labels.json"
camp1359={0:"Items",1:"Magic",2:"Status",3:"Formation",4:"AA Setup",5:"Requests",
6:"Alchemy",7:"Automata",8:"Stone Fusion",9:"Camp",10:"Mage Magic",11:"Prs. Magic",
12:"Key Items",13:"Materials",14:"Identify",15:"AA Setup"}
for i,eng in camp1359.items():
    w=RT["R1359"][i];rd,sz,fl=m_fit_render(eng,w)
    add(FCAMP,f"R1359/{i}",eng,w,rd,w-2,sz,fl,"camp menu","","","camp")
camp1367={18:"Results",19:"Items Held",20:"Client",21:"Reward",22:"Due Date",23:"Storage",
24:"All",25:"Swap Rows",26:"Conf. Day",32:"Sw.",34:"L2/Sw R2/Cls",35:"Swap",36:"R2 Mv",
43:"L3",44:"Reset"}
for i,eng in camp1367.items():
    w=RT["R1367"][i];rd,sz,fl=m_fit_render(eng,w)
    add(FCAMP,f"R1367/{i}",eng,w,rd,w-2,sz,fl,"quest result","","","camp")
# R1910 fixed plaque 126px, render_label floor 7
camp1910={0:"Save",1:"Load",2:"Options",3:"Return to Title",5:"Save & Quit"}
for i,eng in camp1910.items():
    rd,sz,fl=m_render_label(eng,126,AR,15,7)
    add(FCAMP,f"R1910/{i}",eng,126,rd,124,sz,fl,"system menu","","","camp_banner")

# ===== battle =====
FBAT="data/strip_labels/battle_labels.json"
bat1054={0:"Allied Action",1:"Swap Rows",2:"Flee All",3:"Act Freely",4:"Attack",5:"Defend",
6:"Magic",7:"Mage Magic",8:"Prs. Magic",9:"Item",10:"Dispel",11:"Swap Position",12:"Flee",
13:"Party Action",14:"Steal",15:"AA Setup"}
for i,eng in bat1054.items():
    w=RT["R1054"][i];rd,sz,fl=m_fit_render(eng,w)
    add(FBAT,f"R1054/{i}",eng,w,rd,w-2,sz,fl,"battle menu","","","battle")
bat1360={0:"AA Set",1:"Remove All",2:"Undo",3:"Done",4:"Attack AA",5:"Defense AA",6:"Support AA",7:"Magic AA"}
for i,eng in bat1360.items():
    w=RT["R1360"][i];rd,sz,fl=m_fit_render(eng,w)
    add(FBAT,f"R1360/{i}",eng,w,rd,w-2,sz,fl,"AA setup","","","battle")
bat1361={0:"W Slash",1:"Stun Smash",2:"Hold Attack",3:"S.J Attack",4:"Slay Crush",
5:"Cross Cage Kill",6:"Front Guard",7:"Magic Shell",8:"Anti-Magic Shell",9:"Mirror Image",
10:"Spread Out",11:"Close Ranks",12:"Covering Shot",13:"Support Fire",14:"Magic Cancel",
15:"Breath Cancel",16:"Back Cover",17:"Intercept",18:"Spell Focus",19:"Break Silence"}
for i,eng in bat1361.items():
    w=RT["R1361"][i];rd,sz,fl=m_fit_render(eng,w)
    add(FBAT,f"R1361/{i}",eng,w,rd,w-2,sz,fl,"AA skill (glossary.alleid_attacks)","","","battle")
bat1362={0:"Rapid Cast",1:"Magic Weapon",2:"Magic Assist",3:"Focus Attack",4:"Back Attack",
5:"Gale Slash",6:"Rush",7:"Aerial Assault",8:"Sacred Cross",9:"Warp Attack",10:"Soul Crush",
11:"Sonic Sword",12:"Area Attack",13:"Fake Attack",14:"Moon Iai Slash",15:"Nightmare Quake",
16:"Weak Smash",17:"Double Breath"}
for i,eng in bat1362.items():
    w=RT["R1362"][i];rd,sz,fl=m_fit_render(eng,w)
    add(FBAT,f"R1362/{i}",eng,w,rd,w-2,sz,fl,"AA skill (glossary.alleid_attacks)","","","battle")
bat1363={71:"Detail",72:"Set",75:"Remove",73:"AP Select",80:"Back",82:"Catch",60:"Skill"}
for i,eng in bat1363.items():
    w=RT["R1363"][i];rd,sz,fl=m_fit_render(eng,w)
    add(FBAT,f"R1363/{i}",eng,w,rd,w-2,sz,fl,"battle UI","","","battle")
# freeform bond kanji 24px cells, render_label floor 7, start 8
bat1363f={21:"Bond",22:"Oath",23:"Trst",24:"Frnd",25:"Symp",26:"Duty",27:"Ally",28:"Dbt",29:"Hate"}
for i,eng in bat1363f.items():
    w=RT["R1363"][i];rd,sz,fl=m_render_label(eng,w,AR,8,7)
    add(FBAT,f"R1363/{i} freeform",eng,w,rd,w-2,sz,fl,"bond gauge","","","battle_ff")
bat1364={28:"Req.",29:"Front",30:"Back"}
for i,eng in bat1364.items():
    w=RT["R1364"][i];rd,sz,fl=m_fit_render(eng,w)
    add(FBAT,f"R1364/{i}",eng,w,rd,w-2,sz,fl,"battle row","","","battle")

# ===== R1365 (serif, w-2, floor 9, start 11 for h<32) =====
F1365="data/strip_labels/r1365_labels.json"
r1365={4:"Race",5:"Sex",6:"Align",7:"Class",8:"Nature",9:"Atk",10:"Def",11:"Eva",
12:"Str",13:"Int",14:"Pie",15:"Vit",16:"Agi",17:"Lck",18:"Accuracy",22:"Status",
23:"Mage Magic",24:"Prs. Magic",25:"Items",26:"Items",27:"Key Items",28:"Materials",
29:"Items",38:"Library",39:"Camp",41:"System",43:"Convert",44:"Potential",45:"Detail",
46:"Order",47:"Switch",48:"Requests",49:"Storage",50:"Poison",51:"Numb",52:"Fear",
53:"Dead",54:"Stone",55:"Ash",56:"Possessed",78:"Expires",79:"d"}
for i,eng in r1365.items():
    w=RT["R1365"][i];rd,sz,fl=m_r1365(eng,w,11)
    add(F1365,f"R1365/{i}",eng,w,rd,w-2,sz,fl,"status bar","","","r1365")

# ===== R2147 (label.w - 2, floor 7, per-label font) =====
F2147="data/strip_labels/r2147_labels.json"
r2147=[("tavern_submenu/0","Go Outside",128),("tavern_submenu/1","Message Board",128),
("tavern_submenu/2","Requests",128),("tavern_submenu/3","Personal Deeds",128),
("tavern_submenu/4","Trap Game",128),("tavern_submenu/5","Bar Luna Light",128),
("tavern_submenu/6","Practice",128),("tavern_submenu/7","Game",128),
("tavern_submenu/8","Prize Exchange",128),("bulletin_hint/0","L1/R1 Switch",105),
("bulletin_hint/1","Next Page",70),("bulletin_hint/2","OK",50),
("bulletin_hint/3","Back",41),("bulletin_hint/4","Switch",51)]
for nm,eng,w in r2147:
    rd,sz,fl=m_render_label(eng,w,AR,13,7)
    add(F2147,nm,eng,w,rd,w-2,sz,fl,"tavern submenu / bulletin","","","r2147")

# ===== R1370 (cell.w - 2, floor 7, start 14) =====
F1370="data/strip_labels/r1370_labels.json"
r1370=[("R1370/絆","Bond",42),("R1370/誓","Pledge",41),("R1370/信","Trust",42),
("R1370/友","Friends",43),("R1370/情","Sympathy",42),("R1370/義","Duty",42),
("R1370/盟","Alliance",41),("R1370/疑","Doubt",42),("R1370/憎","Hate",43),("R1370/不","Broken",42)]
for nm,eng,w in r1370:
    rd,sz,fl=m_render_label(eng,w,AR,14,7)
    add(F1370,nm,eng,w,rd,w-2,sz,fl,"trust medallion","","","r1370")

json.dump(res,open("build/_audit_out.json","w"),indent=1)
# print summary
ov=[r for r in res if r["status"]=="overflow"]
nm=[r for r in res if r["status"]=="near-miss"]
print("TOTAL",len(res),"OVERFLOW",len(ov),"NEARMISS",len(nm))
print("=== OVERFLOW ===")
for r in ov:print(r["name"],"|",repr(r["english"]),"| rect",r["rect_w"],"rendered",r["rendered_px"],"budget",r["budget_px"],"size",r["final_size"],"floorhit",r["floor_hit"])
print("=== NEAR-MISS ===")
for r in nm:print(r["name"],"|",repr(r["english"]),"| rect",r["rect_w"],"rendered",r["rendered_px"],"budget",r["budget_px"],"size",r["final_size"])
