import os,struct,sys,json
sys.stdout.reconfigure(encoding='utf-8')
BASE=r"C:\programmieren\wizardrytranslation"
sys.path.insert(0,os.path.join(BASE,"tools"))
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets
opt=json.load(open(os.path.join(BASE,"build","recon_v85","exe-interpreter","opcode_table_v85.json")))
OPLEN={int(k,16):v["bytes"] for k,v in opt["opcodes"].items()}
def load(res):
    raw=open(os.path.join(BASE,"extracted","packdata_raw",f"{res:04d}_type02.raw"),'rb').read()
    sec2_off=struct.unpack_from('<I',raw,0x18)[0]
    sec1=raw[0x20:sec2_off]
    sec2=raw[sec2_off:sec2_off+struct.unpack_from('<I',raw,0x14)[0]]
    groups,_=parse_sec2_group_offsets(sec2)
    return sec1,groups
res=1197
sec1,groups=load(res)
ok,instrs=walk(sec1)
print("walk ok:",ok,"n instrs:",len(instrs))
# census of opcodes from the BFS walk
from collections import Counter
c=Counter()
for ins in instrs:
    c[ins['op'] if 'op' in ins else ins.get('opcode')]+=1
print("opcode census (BFS walk):")
for op,n in sorted(c.items()):
    print(f"  {op:#04x}: {n}")
# show structure of one instr
print("sample instr:",instrs[0])
