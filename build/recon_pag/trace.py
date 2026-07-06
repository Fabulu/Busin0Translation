import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from sec1_disasm import walk
import patch_section1_offsets as P
from spans import load, groups_in_span
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]
res=int(sys.argv[1]); lo=int(sys.argv[2],0); hi=int(sys.argv[3],0)
ok,instrs,sec1,groups,words=load(res)
NAMES={0x04:'DISPLAY_TEXT',0x0C:'SET_NAME(spk)',0x0D:'CLR_NAME',0x14:'LABEL',0x60:'ACT_CENTER'}
for pc in sorted(instrs):
    if pc<lo or pc>hi: continue
    op=instrs[pc]
    extra=''
    if op==0x04:
        off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
        gis=groups_in_span(groups,off,cnt)
        extra=f' off={off} cnt={cnt} groups={gis[0]}..{gis[-1]}' if gis else f' off={off} cnt={cnt}'
    elif op==0x14:
        extra=f' param={beu16(sec1,pc+2)} off={beu32(sec1,pc+6)} cnt={beu32(sec1,pc+10)}'
    elif op==0x60:
        extra=f' param={beu16(sec1,pc+2)}'
    elif op in(0x0C,0x0D):
        extra=f' param={beu16(sec1,pc+2)} idx={beu16(sec1,pc+4)}'
    if op in NAMES:
        print("  S1+0x%04X  op=0x%02X %-14s%s"%(pc,op,NAMES.get(op,''),extra))
