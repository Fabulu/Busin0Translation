import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
exe=open("extracted/SLPM_653.78","rb").read()
def f(va): return va-0x100000+0x80
base=0x4CA710
print("page table entries 88..120 (looking for non-font/portrait resources):")
for i in range(88,130):
    w=struct.unpack_from("<I",exe,f(base)+i*4)[0]
    res=w>>16
    print(f"  page {i:3d}: 0x{w:08X} -> R{res}" + (" (EMPTY)" if w==0 else ""))
