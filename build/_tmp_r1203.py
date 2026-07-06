import struct, os, sys, json
ROOT=os.path.abspath("."); sys.path.insert(0,os.path.join(ROOT,"tools"))
import sec1_disasm as S
GM=json.load(open("data/msg_glyph_map.json",encoding="utf-8"))
d=open("extracted/packdata_raw/1203_type02.raw","rb").read()
ok,instrs,sec1,sec2_off=S.walk_resource(d); recs=S.extract_records(sec1,instrs)
sec2=d[sec2_off:]; n=len(sec2)//2
# group starts
gs=[];start=0
for i in range(n):
    if struct.unpack_from(">H",sec2,i*2)[0]==0xFFFF: gs.append(start);start=i+1
gset=set(gs)
labeloff={r["off"]:r["cnt"] for r in recs["label"]}
T4=tuple([297,280,286,290])
for g in gs:
    seq=tuple(struct.unpack_from(">H",sec2,(g+i)*2)[0] for i in range(min(4,n-g)))
    if seq==T4:
        # is there a 0x14 record at this group start? what cnt?
        lc=labeloff.get(g,"NO-0x14-record")
        print("group@%d starts KISHIDANCHO; 0x14 cnt=%s"%(g,lc))
