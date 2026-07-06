import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_pag')
from spans import load, groups_in_span
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]
res=int(sys.argv[1]); want_off=int(sys.argv[2]); want_cnt=int(sys.argv[3])
ok,instrs,sec1,groups,words=load(res)
for pc in sorted(instrs):
    if instrs[pc]==0x04:
        off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
        if off==want_off and cnt==want_cnt:
            print("R%d block off=%d cnt=%d at S1+0x%04X"%(res,off,cnt,pc))
