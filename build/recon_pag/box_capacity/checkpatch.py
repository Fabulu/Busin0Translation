import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_cine/extract/overflowbartalk__ee.bin','rb').read()
print('ee size',len(ee), hex(len(ee)))
# EXE loads at vaddr 0x100000 in EE RAM. The instruction at VA 0x3079DC lives at EE offset 0x3079DC (RAM is flat from 0).
for va in [0x3079DC, 0x307510, 0x305b1c]:
    if va < len(ee):
        w=struct.unpack_from('<I',ee,va)[0]
        print('VA %08x -> EE word %08x'%(va,w))
# the pitch instr
w=struct.unpack_from('<I',ee,0x3079DC)[0] if 0x3079DC<len(ee) else None
print('pitch instr at 0x3079DC =', hex(w) if w else 'OOR', '-> imm', hex(w&0xffff) if w else '')
