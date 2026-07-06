import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def getdat(p,name):
    z=zipfile.ZipFile(p)
    return z.read(name)
for lbl,p in [('WORKING','tavern104.p2s'),('FROZEN','fuckinghellman.p2s')]:
    dat=getdat('C:/programmieren/wizardrytranslation/ramdumps/'+p,'PCSX2 Internal Structures.dat')
    # PCSX2 cpuRegs: GPRs(32*16) then HI,LO,sa? then pc. The struct 'cpuRegs' starts with GPR[32] as 128-bit each.
    # Heuristic: scan for a plausible EE PC (0x00xxxxxx in code range 0x100000-0x500000) near a 'cpuRegs' marker.
    # The savestate stores freezeData blocks with tags. Search for 'eeCpu' / scan for pc field.
    # Simpler: find the cpuRegs GPR block: GPR[0] (zero reg) is 16 bytes of 0. pc usually follows GPRs+HI+LO+sa.
    # Search candidate pc values in code range, aligned, that appear right after a 16-byte zero (zero reg) far in.
    cands=[]
    for i in range(0, len(dat)-4, 4):
        v=struct.unpack('<I',dat[i:i+4])[0]
        if 0x100000<=v<0x600000:
            cands.append((i,v))
    print(f'{lbl}: dat size {len(dat)}; #pc-range words {len(cands)}')
