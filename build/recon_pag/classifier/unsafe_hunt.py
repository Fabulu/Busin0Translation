import sys, os, struct, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]

# Refined classifier modeling the OBSERVED named-utterance shape:
#   NAMELBL(slot P)  ...  OP60 v=P(>=1)  DISPLAY(name)  OP60 v=0  DISPLAY(body...)
# Rule: a DISPLAY block is DIALOGUE iff it lies within the "named utterance" that
# began at a NAMELBL and is still active. The utterance is considered active from
# the NAMELBL until the next NAMELBL OR until a DISPLAY appears that is NOT
# immediately preceded (in the op stream, ignoring DISPLAY) by an OP60.
# Simpler operational form used in build: window K with NAMELBL.
#
# Here we hunt the UNSAFE direction: among resources that walk OK, list every
# DISPLAY block with since<=1 (would be paginated) and dump whether an OP60 v>=1
# (named-speaker activation) exists in its lineage since the last NAMELBL.

paths=sorted(glob.glob('extracted/packdata_raw/*_type02.raw'))
flagged=[]
for p in paths:
    data=open(p,'rb').read()
    ok,instrs,sec1,s2=S.walk_resource(data)
    if not ok: continue
    groups,_=P.parse_sec2_group_offsets(data[s2:])
    recs=S.extract_records(sec1,instrs)
    disp={d['pc']:d for d in recs['display']}
    name_pcs={r['pc'] for r in recs['label']}
    since=99; saw_named_op60=False; out=[]
    for pc in sorted(instrs):
        op=instrs[pc]
        if op==0x14:
            since=0; saw_named_op60=False
        elif op==0x60:
            v=beu16(sec1,pc+2)
            if v>=1 and v<10: saw_named_op60=True
        elif op==0x04 and pc in disp and disp[pc]['cnt']>0:
            d=disp[pc]; gf=P._find_group(groups,d['off']);gl=P._find_group(groups,d['off']+d['cnt']-1)
            out.append((gf,gl,since,saw_named_op60,d['cnt']))
            since+=1
    # report blocks with since<=1 that LACK a named-op60 in lineage (suspicious dialogue calls)
    for gf,gl,s,named,cnt in out:
        if s<=1 and not named:
            flagged.append((os.path.basename(p),gf,gl,s,cnt))
print(f"Blocks with since<=1 but NO named-op60(v>=1) in lineage: {len(flagged)}")
for f in flagged[:40]:
    print("  ",f)
