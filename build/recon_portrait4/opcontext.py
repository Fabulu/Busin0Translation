import sys, struct, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from patch_section1_offsets import walk, extract_records, HEADER_SIZE
RAW='extracted/packdata_raw'
raw=open(f'{RAW}/1196_type02.raw','rb').read()
s2s=struct.unpack_from('<I',raw,0x14)[0];s2o=struct.unpack_from('<I',raw,0x18)[0]
sec1=raw[HEADER_SIZE:s2o]
ok,instrs=walk(sec1)
recs=extract_records(sec1,instrs)
# map group index -> word offset start. Build group offsets.
sec2=raw[s2o:s2o+s2s];n=len(sec2)//2
words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
grps=[];start=0
for i in range(n):
    if words[i]==0xFFFF: grps.append(words[start:i]);start=i+1
goff=[];p=0
for gg in grps:
    goff.append(p);p+=len(gg)+1
# For target groups, find the 0x04 display record whose off == group start
disp=recs['display']
# instrs is list; build pc->opcode for context. Re-walk to get opcode sequence
op_table=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json',encoding='utf-8')) if os.path.isfile('build/recon_v85/exe-interpreter/opcode_table_v85.json') else None
def op_at(pc):
    return struct.unpack_from('>H',sec1,pc)[0]
for gi in [575,577,583,925 if False else 569]:
    if gi>=len(goff): continue
    woff=goff[gi]
    # find display record with off==woff
    rec=[d for d in disp if d['off']==woff]
    print(f"--- g{gi} word_off={woff} display_recs={rec}")
    if rec:
        pc=rec[0]['pc']
        # print 8 opcodes before pc
        # need instr boundaries; use instrs list of (pc,len)?
        # instrs format unknown; print raw words around pc
        ctx=[op_at(pc-2*k) for k in range(6,0,-1)]
        print(f"   words before pc=0x{pc:X}:", ' '.join(f'{w:04X}' for w in ctx))
        print(f"   word at pc:", f'{op_at(pc):04X}')
