import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("RAMdumps/stillbad-5_eeMemory.bin","rb").read()
def u32(a): return struct.unpack_from("<I",ee,a)[0]
def u16(a): return struct.unpack_from("<H",ee,a)[0]
# Known global VAs (EE offset = vaddr):
print("sec1_base @0x564ED0 =", hex(u32(0x564ED0)))
print("sec2_base @0x564ED4 =", hex(u32(0x564ED4)))
# gp-relative globals: gp-0x68E4=struct_base, gp-0x68E8=page_array, gp-0x68D0=glyph_id, gp-0x68CC=slotcount, gp-0x68C8=state
# These live near each other. sec1_base_global is at 0x564ED0 (absolute, not gp). 
# gp itself: the sdata globals. The struct base ptr global VA = gp-0x68E4. 
# We don't know gp, but the sbss block with these globals is contiguous. 
# Let's find gp by: the page_array global (gp-0x68E8) and struct global (gp-0x68E4) are 4 bytes apart,
# both heap pointers. Scan sbss region (around 0x55E000..0x575000) for two adjacent u32 heap ptrs.
print("--- scanning for adjacent heap pointers (page_array, struct_base) in sbss ---")
for va in range(0x558000,0x575000,4):
    a=u32(va); b=u32(va+4)
    if 0x100000<=a<0x02000000 and 0x100000<=b<0x02000000:
        # candidate: gp-0x68E8=va(page_array), gp-0x68E4=va+4(struct). gp=va+0x68E8
        gp=va+0x68E8
        # validate: gp-0x68D0 (glyph_id) should be a u16 <0x2A7; gp-0x68CC slotcount <32
        gid=u16(gp-0x68D0); sc=u16(gp-0x68CC); st=u16(gp-0x68C8)
        if gid<0x2A7 and sc<=32 and st<=4:
            print(f"  va=0x{va:08X} gp=0x{gp:08X} page_arr=0x{a:08X} struct=0x{b:08X} glyph_id={gid} slotcount={sc} state={st}")
