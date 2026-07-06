import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I", ee, a)[0]
# gp is set via lui/addiu somewhere; the main loop uses gp-relative addressing.
# Common: gp base for this game. The handler-table indexing used lui 0x4d, addiu -27808 => 0x4D0000-0x6CA0=0x4C9360 (abs). 
# gp-relative globals: gp-26928 (run flag), gp-26920 (last handler). We need gp.
# gp typically = _gp symbol. The sw zero,-26928(gp) etc. Let's find gp from the saved $gp register?
# The EE save bin is raw RAM only (no registers). But gp is a constant the EXE sets at boot: lui gp; addiu gp.
# Search EXE for the gp setup near _start. Instead infer: handler table abs 0x4C9360. gp-relative base = ?
# The game's small-data area (sdata) is around 0x4Fxxxx (we saw lui a0,0x4f addiu a0,a0,14592 => 0x4F0000+14592=0x4F3900 strings).
# gp = 0x4F8000-ish typically (sdata midpoint). gp-26928 = gp-0x6930.
# Let's brute: find candidate gp such that gp-26928 holds 0 (run finished) and gp-26920 holds a valid handler va (in 0x2Fxxxx).
for gp in range(0x4F0000, 0x500000, 0x10):
    h=u32((gp-26920)&0x1ffffff)
    if 0x2F0000 <= h <= 0x2FFFFF:
        run=u32((gp-26928)&0x1ffffff)
        print("gp=%08X last_handler=%08X runflag=%08X"%(gp,h,run))
