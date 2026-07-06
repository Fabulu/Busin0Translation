import os,struct,sys,json
sys.stdout.reconfigure(encoding='utf-8')
BASE=r"C:\programmieren\wizardrytranslation"
sys.path.insert(0,os.path.join(BASE,"tools"))
from patch_section1_offsets import parse_sec2_group_offsets
opt=json.load(open(os.path.join(BASE,"build","recon_v85","exe-interpreter","opcode_table_v85.json")))
OPLEN={int(k,16):v["bytes"] for k,v in opt["opcodes"].items()}
N_OPS=193
def load(res):
    raw=open(os.path.join(BASE,"extracted","packdata_raw",f"{res:04d}_type02.raw"),'rb').read()
    so=struct.unpack_from('<I',raw,0x18)[0]
    sec1=raw[0x20:so]
    sec2=raw[so:so+struct.unpack_from('<I',raw,0x14)[0]]
    groups,_=parse_sec2_group_offsets(sec2)
    return sec1,groups
def be16(b,o):return (b[o]<<8)|b[o+1]
def be32(b,o):return (b[o]<<24)|(b[o+1]<<16)|(b[o+2]<<8)|b[o+3]
JUMP={0x08,0x0b}
COND={0x06,0x07}
GOSUB={0x03}  # gosub-ish (0x03 op+u16+u32) - treat as call w/ fallthrough? keep simple: treat as fallthrough

def trace(res):
    sec1,groups=load(res)
    n=len(sec1)
    # state = (dlgflag bit0, nameidx_set bool). BFS; at each pc store best-known incoming state; revisit if state changes.
    # We OR-merge dialogue-ness (if any path reaches a 0x04 in dialogue state -> dialogue).
    seen={}  # pc -> set of states visited
    disp={}  # off(0x04 operand) -> 'D'/'N' (D if any path dialogue)
    work=[(0,0,0)]  # pc, dlg, name
    while work:
        pc,dlg,name=work.pop()
        if pc<0 or pc+2>n: continue
        st=(dlg,name)
        if pc in seen and st in seen[pc]: continue
        seen.setdefault(pc,set()).add(st)
        op=be16(pc:=pc, o=pc) if False else be16(sec1,pc)
        if op>=N_OPS: continue
        ln=OPLEN.get(op,2)
        if ln<2: ln=2
        # state transitions
        if op==0x21: dlg=1
        elif op==0x22: dlg=0
        elif op==0x60: name=1
        elif op==0x04 and pc+10<=n:
            off=be32(sec1,pc+2)
            d='D' if (dlg or name) else 'N'
            prev=disp.get(off)
            disp[off]='D' if (prev=='D' or d=='D') else 'N'
            disp.setdefault(off,d)
        # control flow
        if op in JUMP and pc+6<=n:
            t=be32(sec1,pc+2)
            work.append((t,dlg,name)); continue
        if op in COND and pc+14<=n:
            t=be32(sec1,pc+10)
            work.append((t,dlg,name))
            work.append((pc+ln,dlg,name)); continue
        work.append((pc+ln,dlg,name))
    # map 0x04 off -> groups
    result={}
    for off,d in disp.items():
        # need cnt; redo: store cnt too. Recompute by scanning. Simpler: store cnt in disp
        pass
    return disp,groups

def trace_full(res):
    sec1,groups=load(res)
    n=len(sec1)
    seen={}
    disp={}  # off -> [d, cnt]
    work=[(0,0,0)]
    while work:
        pc,dlg,name=work.pop()
        if pc<0 or pc+2>n: continue
        st=(dlg,name)
        if pc in seen and st in seen[pc]: continue
        seen.setdefault(pc,set()).add(st)
        op=be16(sec1,pc)
        if op>=N_OPS: continue
        ln=OPLEN.get(op,2) or 2
        if op==0x21: dlg=1
        elif op==0x22: dlg=0
        elif op==0x60: name=1
        elif op==0x04 and pc+10<=n:
            off=be32(sec1,pc+2); cnt=be32(sec1,pc+6)
            d='D' if (dlg or name) else 'N'
            if off in disp:
                if d=='D': disp[off][0]='D'
            else: disp[off]=[d,cnt]
        if op in JUMP and pc+6<=n:
            t=be32(sec1,pc+2); work.append((t,dlg,name)); continue
        if op in COND and pc+14<=n:
            t=be32(sec1,pc+10)
            work.append((t,dlg,name)); work.append((pc+ln,dlg,name)); continue
        work.append((pc+ln,dlg,name))
    result={}
    for off,(d,cnt) in disp.items():
        if cnt==0: continue
        end=off+cnt
        for gi,(gs,ge) in enumerate(groups):
            if not(ge<off or gs>=end):
                # OR: dialogue wins
                if gi in result and result[gi]=='D': continue
                result[gi]=d
    return result

for res in (1196,1197):
    r=trace_full(res)
    print(f"R{res}: {len(r)} groups; D={sum(1 for v in r.values() if v=='D')} N={sum(1 for v in r.values() if v=='N')}")

r1197=trace_full(1197); r1196=trace_full(1196)
print("\n--- GROUND TRUTH ---")
def ck(r,res,gs,exp):
    for g in gs:
        got=r.get(g,'-')
        print(f"R{res} g{g} expect {exp} got {got} {'OK' if got==exp else 'XX'}")
ck(r1197,1197,[904,4,9,10,922,925,927,929],'D')
ck(r1197,1197,[3,7,13,926],'N')
ck(r1196,1196,[569,575,616],'N')
