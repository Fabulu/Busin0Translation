import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk, LENB
import patch_section1_offsets as P

RAW='extracted/packdata_raw'

def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def analyze(res_idx):
    path=f'{RAW}/{res_idx:04d}_type02.raw'
    if not os.path.isfile(path): return None
    data=open(path,'rb').read()
    sec2_off=struct.unpack_from('<I',data,0x18)[0]
    sec2_size=struct.unpack_from('<I',data,0x14)[0]
    sec1=data[0x20:sec2_off]
    sec2=data[sec2_off:sec2_off+sec2_size]
    ok,instrs=walk(sec1)
    groups,trail=P.parse_sec2_group_offsets(sec2)
    # walk instrs in PC order; track active centered slot state.
    # Model: [0x298] starts -1 (boxed). opcode 0x60 sets it to its param.
    #        a 0x14 with param=k populates slot k.
    # mode-2 (centered) for a 0x04 fires iff active298 != -1 (and slot populated).
    pcs=sorted(instrs)
    active298=-1          # current centered slot, -1=boxed
    populated=set()       # 0x14 slots populated
    has_60=False
    results=[]            # per 0x04: (pc, off, cnt, gi, mode)
    n_60=0; n_14=0; n_04=0; n_0c=0
    for pc in pcs:
        op=instrs[pc]
        if op==0x60:
            n_60+=1; has_60=True
            param=beu16(sec1,pc+2)
            active298=param
        elif op==0x14:
            n_14+=1
            param=beu16(sec1,pc+2)
            if param<10: populated.add(param)
        elif op in (0x0C,0x0D):
            n_0c+=1
        elif op==0x04:
            n_04+=1
            off=beu32(sec1,pc+2); cnt=beu32(sec1,pc+6)
            gi=P._find_group(groups,off) if cnt>0 else None
            centered = (active298!=-1 and active298 in populated)
            mode = 2 if centered else 0
            results.append({'pc':pc,'off':off,'cnt':cnt,'gi':gi,'mode':mode})
    return {'res':res_idx,'ok':ok,'n04':n_04,'n14':n_14,'n60':n_60,'n0c':n_0c,
            'has_60':has_60,'ngroups':len(groups),'results':results,
            'groups':groups,'sec2':sec2}

if __name__=='__main__':
    for r in [int(x) for x in sys.argv[1:]]:
        a=analyze(r)
        if a is None: print(r,'(no type02)'); continue
        nc=sum(1 for x in a['results'] if x['mode']==2)
        nb=sum(1 for x in a['results'] if x['mode']==0)
        print("R%d ok=%s groups=%d  0x04=%d (boxed=%d centered=%d)  0x60=%d 0x14=%d 0x0C/D=%d"
              %(r,a['ok'],a['ngroups'],a['n04'],nb,nc,a['n60'],a['n14'],a['n0c']))
