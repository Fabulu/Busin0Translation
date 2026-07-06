import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
TAB=0x4C9360
ents=[struct.unpack('<I',exe[TAB-VA_BASE+i*4:TAB-VA_BASE+i*4+4])[0] for i in range(193)]
sh=sorted(set(h for h in ents if 0x2F0000<h<0x310000))
def owner(va):
    cand=[h for h in sh if h<=va]
    if not cand: return None
    h=max(cand)
    return h,[i for i,hh in enumerate(ents) if hh==h]
# scan for sw to 0x290 then look at preceding few ops to decide set bit0 / clear bit0 / =0 / =2
va=0x2F0000
while va<0x300000:
    w=struct.unpack('<I',exe[va-VA_BASE:va-VA_BASE+4])[0]
    op=(w>>26)&0x3F; rt=(w>>16)&0x1F; imm=w&0xFFFF; s=imm-0x10000 if imm&0x8000 else imm
    if op==0x2B and s==0x290:
        # look back up to 4 instrs for ori/andi/li that set rt
        ctx=[]
        for k in range(1,6):
            pw=struct.unpack('<I',exe[va-VA_BASE-4*k:va-VA_BASE-4*k+4])[0]
            ctx.append(pw)
        # classify
        kind='?'
        for pw in ctx:
            pop=(pw>>26)&0x3F; prt=(pw>>16)&0x1F; pimm=pw&0xFFFF; ps=pimm-0x10000 if pimm&0x8000 else pimm
            if pop==0x0D and pimm==1: kind='SET bit0 (ori|1)';break   # ori ,,1
            if pop==0x09 and (pw>>21&0x1f)==0 and ps in (0,2): kind=f'LI {ps}';break
            if pop==0x0C: kind=f'ANDI mask {pimm:#x} (clear)';break
        o=owner(va)
        ops=[hex(x) for x in o[1]] if o else '?'
        print(f"{va:08X}  handler ops {ops}  -> {kind}")
    va+=4
