import struct, glob, os, sys, json
ROOT=os.path.abspath(".")
sys.path.insert(0, os.path.join(ROOT,"tools"))
import sec1_disasm as S
RAW=os.path.join(ROOT,"extracted","packdata_raw")
def groups_of(sec2):
    n=len(sec2)//2;g=[];start=0
    for i in range(n):
        if struct.unpack_from(">H",sec2,i*2)[0]==0xFFFF:g.append((start,i));start=i+1
    return g,start
T4=tuple([297,280,286,290]); T3=tuple([297,280,286])
for rid in ["1194","1196","1197","1198","1203","1354"]:
    p=os.path.join(RAW,rid.zfill(4)+"_type02.raw"); d=open(p,"rb").read()
    try: ok,instrs,sec1,sec2_off=S.walk_resource(d)
    except Exception as e: print("R%s FAIL"%rid); continue
    sec2=d[sec2_off:]; groups,trail=groups_of(sec2)
    # check group starts for the 4/3 sequence
    g4=g3=0
    for gs,ge in groups:
        seq=tuple(struct.unpack_from(">H",sec2,(gs+i)*2)[0] for i in range(min(4,ge-gs)))
        if seq[:4]==T4: g4+=1
        elif seq[:3]==T3: g3+=1
    print("R%-5s group-prefix KISHIDANCHO=%d  KISHIDAN-only=%d"%(rid,g4,g3))
