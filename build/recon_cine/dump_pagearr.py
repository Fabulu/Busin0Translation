import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("RAMdumps/stillbad-5_eeMemory.bin","rb").read()
exe=open("extracted/SLPM_653.78","rb").read()
def u32e(a): return struct.unpack_from("<I",ee,a)[0]
def u16e(a): return struct.unpack_from("<H",ee,a)[0]
def f(va): return va-0x100000+0x80
# static page table at 0x4CA710 (read from EXE), 4-byte handles
def stat_handle(i): return struct.unpack_from("<I",exe,f(0x4CA710)+i*4)[0]
for base in (0x5078F8, 0x506510):
    print(f"=== page array @ 0x{base:08X} ===")
    for i in range(0,100):
        p=u32e(base+i*8); rc=u16e(base+i*8+4)
        if p!=0:
            h=stat_handle(i); res=h>>16
            print(f"  page[{i:3d}] ptr=0x{p:08X} rc={rc}  static_handle=0x{h:08X} -> R{res}")
