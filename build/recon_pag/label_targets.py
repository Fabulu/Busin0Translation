import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
import patch_section1_offsets as P
from sec1_disasm import extract_records
from spans import load
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]
res=int(sys.argv[1]); gis=set(int(x) for x in sys.argv[2:])
ok,instrs,sec1,groups,words=load(res)
recs=extract_records(sec1,instrs)
# which groups do 0x14 labels target, and which do 0x04 target
def span_groups(off,cnt):
    end=off+cnt; out=[]
    for gi,(gs,ge) in enumerate(groups):
        if gs<end and ge>=off: out.append(gi)
    return out
print("--- 0x14 LABEL targets hitting groups",sorted(gis),"---")
for r in recs['label']:
    sg=span_groups(r['off'],r['cnt'])
    if gis & set(sg):
        print("  0x14 param=%d off=%d cnt=%d -> groups %s"%(r['param'],r['off'],r['cnt'],sg))
print("--- 0x04 DISPLAY targets hitting groups",sorted(gis),"---")
for r in recs['display']:
    if r['cnt']==0: continue
    sg=span_groups(r['off'],r['cnt'])
    if gis & set(sg):
        print("  0x04 off=%d cnt=%d -> groups %s"%(r['off'],r['cnt'],sg))
