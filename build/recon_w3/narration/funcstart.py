import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
# walk backward to find 'addiu $sp,$sp,-N' (prologue) before va
va=int(sys.argv[1],16)
for cur in range(va,va-0x2000,-4):
    o=va2off(cur); w=struct.unpack('<I',data[o:o+4])[0]
    op=w>>26
    if op==0x09: # addiu
        rt=(w>>16)&0x1f; rs=(w>>21)&0x1f; imm=w&0xffff
        if imm>=0x8000: imm-=0x10000
        if rt==29 and rs==29 and imm<0:
            print(f"PROLOGUE 0x{cur:08x}: addiu $sp,$sp,{imm}")
            break
