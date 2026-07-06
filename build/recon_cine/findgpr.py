import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
d=open("RAMdumps/Nameentrystate_extracted/PCSX2 Internal Structures.dat","rb").read()
# EE GPR array: 32 entries x 16 bytes = 512 bytes. r0 must be 0 (16 zero bytes).
# Followed (in cpuRegs) by HI,LO (16 each), sa, IsDelaySlot, pc, code, CP0...
# We look for: 16 zero bytes at start, then nonzero regs, and somewhere a u32 pc in 0x100000..0x500000.
best=[]
for off in range(0, len(d)-512, 4):
    # r0 zero
    if d[off:off+16]!=b'\x00'*16: continue
    # gp = r28 -> off + 28*16 ; low 32 bits
    gp=struct.unpack_from("<I",d,off+28*16)[0]
    sp=struct.unpack_from("<I",d,off+29*16)[0]
    ra=struct.unpack_from("<I",d,off+31*16)[0]
    # sanity: gp in program range, sp in stack range (~0x01Fxxxxx or 0x0xxxxxxx)
    if 0x400000<=gp<=0x600000 and 0x100000<=ra<=0x520000:
        best.append((off,gp,sp,ra))
for off,gp,sp,ra in best[:20]:
    print(f"off=0x{off:X} gp=0x{gp:08X} sp=0x{sp:08X} ra=0x{ra:08X}")
print(len(best),"candidates")
