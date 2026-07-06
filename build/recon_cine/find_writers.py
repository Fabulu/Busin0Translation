import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78","rb").read()
# find all instructions that reference gp-26852 (the struct base) and gp-26856 (page table)
# imm -26852 = 0x97DC as signed16? -26852 & 0xFFFF
t1=(-26852)&0xFFFF
t2=(-26856)&0xFFFF
t3=(-26890)&0xFFFF  # used in 0x2F3450
def va_of(off): return 0x100000+off-0x80
for off in range(0x80,len(data)-4,4):
    w=struct.unpack_from("<I",data,off)[0]
    op=w>>26; rs=(w>>21)&31; imm=w&0xFFFF
    if rs==28 and imm in (t1,t2):  # gp-relative
        which="STRUCT_BASE(-26852)" if imm==t1 else "PAGE_TABLE(-26856)"
        print(f"VA 0x{va_of(off):08X}: gp ref {which} op=0x{op:02X}")
