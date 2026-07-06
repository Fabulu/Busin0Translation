import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
DUMPS={
 'PRESENT':   f'{E2}/Firstdialogue__ee.bin',
 'nshadyman': f'{E}/nshadymanand4linesinsteadof3__ee.bin',
 'nosister':  f'{E}/nosister__ee.bin',
 'ladyknight':f'{E}/ladyknightnoportrait__ee.bin',
}
def load(p): return open(p,'rb').read()
bufs={k:load(v) for k,v in DUMPS.items()}
GP=0x504FF0
PTRADDR=GP-0x68F4   # 0x4FE6FC : pointer to 433-entry u32 array
print(f"scene-var array pointer stored at gp-0x68F4 = 0x{PTRADDR:08X}")
arrbase={}
for k,buf in bufs.items():
    ptr=struct.unpack_from('<I',buf,PTRADDR)[0]
    arrbase[k]=ptr
    print(f"  {k:11s}: array base ptr=0x{ptr:08X}")
print()
# dump the 433-entry u32 array, show non-zero entries
allidx=set()
arrs={}
for k,buf in bufs.items():
    ptr=arrbase[k]
    if not (0<ptr<len(buf)-433*4):
        print(f"  {k}: ptr out of range"); arrs[k]={}; continue
    a={}
    for i in range(433):
        v=struct.unpack_from('<I',buf,ptr+i*4)[0]
        if v: a[i]=v; allidx.add(i)
    arrs[k]=a
print("=== Non-zero scene-var entries (index: value) per dump ===")
for k in DUMPS:
    print(f"  {k:11s}: { {i:hex(arrs[k][i]) for i in sorted(arrs[k])} }")
print()
print("=== Per-index comparison (only where any differs) ===")
for i in sorted(allidx):
    vals={k:arrs[k].get(i,0) for k in DUMPS}
    if len(set(vals.values()))>1:
        print(f"  idx {i:3d}: "+'  '.join(f"{k}={vals[k]:#x}" for k in DUMPS))
