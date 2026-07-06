import os,struct,sys
sys.stdout.reconfigure(encoding='utf-8')
BASE=r"C:\programmieren\wizardrytranslation"
sys.path.insert(0,os.path.join(BASE,"tools"))
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets

# opcode byte-length table
import json
opt=json.load(open(os.path.join(BASE,"build","recon_v85","exe-interpreter","opcode_table_v85.json")))
OPLEN={int(k,16):v["bytes"] for k,v in opt["opcodes"].items()}

def load(res):
    raw=open(os.path.join(BASE,"extracted","packdata_raw",f"{res:04d}_type02.raw"),'rb').read()
    sec2_off=struct.unpack_from('<I',raw,0x18)[0]
    sec2_size=struct.unpack_from('<I',raw,0x14)[0]
    sec1=raw[0x20:sec2_off]
    sec2=raw[sec2_off:sec2_off+sec2_size]
    groups,_=parse_sec2_group_offsets(sec2)
    return sec1,groups

def be16(b,o): return (b[o]<<8)|b[o+1]
def be32(b,o): return (b[o]<<24)|(b[o+1]<<16)|(b[o+2]<<8)|b[o+3]

def classify(res):
    """Linear-walk Section-1 in program order, tracking dialogue flag (bit0).
    op 0x21 sets it, op 0x22 clears it. At each 0x04, record flag -> covered groups.
    Returns dict gi-> 'D' or 'N'. (Linear walk; handles fallthrough. Jumps ignored
    for the persistence model — flag is scene-state.)"""
    sec1,groups=load(res)
    pc=0;flag=0
    result={}
    n=len(sec1)
    disp=[]  # (off,cnt,flag)
    while pc+2<=n:
        op=be16(sec1,pc)
        ln=OPLEN.get(op,2)
        if op==0x21: flag=1
        elif op==0x22: flag=0
        elif op==0x04 and pc+10<=n:
            off=be32(sec1,pc+2); cnt=be32(sec1,pc+6)
            disp.append((off,cnt,flag))
        # bail on unknown/zero length
        if ln<2: ln=2
        pc+=ln
    for off,cnt,fl in disp:
        if cnt==0: continue
        end=off+cnt
        for gi,(gs,ge) in enumerate(groups):
            if not(ge<off or gs>=end):
                result[gi]='D' if fl else 'N'
    return result,disp

for res in (1196,1197):
    r,disp=classify(res)
    print(f"=== R{res}: {len(disp)} 0x04 blocks, {len(r)} groups classified ===")

# ground truth
print("\n--- GROUND TRUTH validation ---")
r1197,_=classify(1197)
r1196,_=classify(1196)
GT_D_1197=[904,4,9,10,922,925,927,929]
GT_N_1197=[3,7,13,926]
GT_N_1196=[569,575,616]
for g in GT_D_1197: print(f"R1197 g{g} expect D got {r1197.get(g,'-')}")
for g in GT_N_1197: print(f"R1197 g{g} expect N got {r1197.get(g,'-')}")
for g in GT_N_1196: print(f"R1196 g{g} expect N got {r1196.get(g,'-')}")
