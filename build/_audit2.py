import json, struct, os
from PIL import ImageFont

RES = "build/packdata_resources"
ARIALBD = "C:/Windows/Fonts/arialbd.ttf"
TIMESBD = "C:/Windows/Fonts/timesbd.ttf"

_fc={}
def F(p,s):
    k=(p,s)
    if k not in _fc: _fc[k]=ImageFont.truetype(p,s)
    return _fc[k]
def W(t,p,s,stroke=0):
    if not t: return 0
    b=F(p,s).getbbox(t,stroke_width=stroke)
    return (b[2]-b[0]) if b else 0

def parse_rects(name,off):
    with open(os.path.join(RES,name),"rb") as f: data=f.read()
    magic,count=struct.unpack_from(">2I",data,off)
    assert magic==5,f"magic {magic} @{off} in {name}"
    out={}
    for i in range(count):
        x,y,w,h,c=struct.unpack_from(">5I",data,off+8+i*20)
        out[i]={"w":w,"h":h}
    return out

RT={}
RT["R1359"]=parse_rects("1359_type02.raw",34656)
RT["R1367"]=parse_rects("1367_type02.raw",35632)
RT["R1054"]=parse_rects("1054_type02.raw",34656)
RT["R1360"]=parse_rects("1360_type02.raw",34656)
RT["R1361"]=parse_rects("1361_type02.raw",34656)
RT["R1362"]=parse_rects("1362_type02.raw",34656)
RT["R1363"]=parse_rects("1363_type02.raw",38560)
RT["R1364"]=parse_rects("1364_type04.raw",35456)
RT["R1365"]=parse_rects("1365_type02.raw",35712)

# dump rect widths for the indices we care about
out={}
for k,v in RT.items():
    out[k]={str(i):v[i]["w"] for i in v}
print(json.dumps(out))
