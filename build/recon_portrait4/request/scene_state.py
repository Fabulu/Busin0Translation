import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EE='build/recon_portrait4/extract/request__ee.bin'
ee=open(EE,'rb').read()
print("EE size", len(ee))
# EXE at RAM 0x100000 => fileoff = vaddr - 0x100000 + 0? Prompt: ".p2s = 32MB EE RAM @ vaddr0=fileoff0"
# So EE RAM byte at vaddr V is at file offset V (vaddr0=fileoff0). EXE loaded at RAM 0x100000.
# gp = 0x00504FF0 . Scene-var array base referenced as gp-0x68F4.
gp=0x00504FF0
def rd32(a): return struct.unpack_from('<I',ee,a)[0]
def rd16(a): return struct.unpack_from('<H',ee,a)[0]
def rd8(a): return ee[a]
print("gp-0x68F4 =", hex(gp-0x68F4), "value(ptr)=", hex(rd32(gp-0x68F4)))
# Resident CG slot
print("CGSLOT 0x509F80 =", hex(rd32(0x509F80)))
# channel flag tables
for n,a in (('p2 0x565090',0x565090),('p1 0x5650D0',0x5650D0),('p0 0x565110',0x565110)):
    print(n, ee[a:a+16].hex())
# Look for a current-resource id. R1197 = 0x4A5. R1196=0x4A4. Search BSS for the loaded resource id near interpreter state.
# Scan a window of gp-relative globals for plausible resource ids 1196/1197
for off in range(-0x8000, 0x4000, 4):
    a=gp+off
    if 0<=a<len(ee)-4:
        v=rd32(a)
        if v in (1196,1197,0x4A4,0x4A5):
            print(f"  gp{off:+#x} (0x{a:X}) = {v}")
