import json, os, struct, sys, glob
ROOT=os.path.abspath(".")
sys.path.insert(0, os.path.join(ROOT,"tools"))
import sec1_disasm as S
RAW=os.path.join(ROOT,"extracted","packdata_raw")
GM=json.load(open(os.path.join(ROOT,"data","msg_glyph_map.json"),encoding="utf-8"))
def gl(s): return s.encode("ascii","backslashreplace").decode("ascii") if s else s
def decode(sec2,off,cnt):
    out=[];n=len(sec2)//2
    for i in range(off,off+cnt):
        if i<0 or i>=n: return None
        g=struct.unpack_from(">H",sec2,i*2)[0]
        if g>=0xFB00 or g==0xFFFF: return None
        ch=GM.get(str(g)); out.append(ch if ch is not None else "?")
    return "".join(out)
def groups_of(sec2):
    n=len(sec2)//2;g=[];start=0
    for i in range(n):
        if struct.unpack_from(">H",sec2,i*2)[0]==0xFFFF:g.append((start,i));start=i+1
    return g,start
# Find every island that decodes to 士騎戦 or 士騎戦動 ; report resource + prefix + which scene
T3="士騎戦"; T4="士騎戦動"
c3=0;c4=0;res3=set();res4=set()
for p in sorted(glob.glob(os.path.join(RAW,"*_type02.raw"))):
    rid=os.path.basename(p).split("_")[0].lstrip("0")
    d=open(p,"rb").read()
    try:
        ok,instrs,sec1,sec2_off=S.walk_resource(d);recs=S.extract_records(sec1,instrs)
    except Exception: continue
    sec2=d[sec2_off:];groups,trail=groups_of(sec2);gstart={gs for gs,ge in groups}
    n=len(sec2)//2
    for r in recs["label"]:
        off,cnt=r["off"],r["cnt"]
        if off+cnt>n: continue
        s=decode(sec2,off,cnt)
        if s==T3: c3+=1;res3.add("R"+rid)
        if s==T4: c4+=1;res4.add("R"+rid)
print("3-glyph KISHIDAN islands:",c3,"in",sorted(res3))
print("4-glyph KISHIDANCHO islands:",c4,"in",sorted(res4))
