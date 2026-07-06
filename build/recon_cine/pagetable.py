import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78","rb").read()
def f(va): return va-0x100000+0x80
# page table at VA 0x4CA710, 4-byte handles? doc says resource_id<<16
base=0x4CA710
print("Page table @ 0x4CA710 (assuming 4-byte entries, handle=res<<16):")
for i in range(0,110):
    w=struct.unpack_from("<I",data,f(base)+i*4)[0]
    if w==0: 
        print(f"  page {i:3d}: 0x{w:08X}  (empty)")
        continue
    res=w>>16
    print(f"  page {i:3d}: 0x{w:08X}  res=R{res} low=0x{w&0xFFFF:04X}")
