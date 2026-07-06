import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
# find $gp value: the EXE sets gp in _start. Common: gp = 0x4dXXXX. The dispatcher used lui 0x4d offsets.
# handler table base = 0x4D0000-0x6ca0 = 0x4C9360. Confirm table entries valid pointers.
tbl=0x4C9360
print("handler[0x04]=0x%08x (expect 0x2F3700)"%struct.unpack_from("<I",ee,tbl+4*4)[0])
print("handler[0x00]=0x%08x"%struct.unpack_from("<I",ee,tbl+0)[0])
print("handler[0x1a]=0x%08x (expect 0x2F4450)"%struct.unpack_from("<I",ee,tbl+0x1a*4)[0])
# gp: from lbu -0x6930(gp). gp is typically the value such that gp-0x6930 = some bss var.
# We can't easily know gp. Instead inspect the script-state object 0x564ed0 fields.
sv=0x564ed0
print("\nstate@0x564ed0:")
for k in range(0,12):
    print("  +0x%02x: 0x%08x"%(k*4,struct.unpack_from("<I",ee,sv+k*4)[0]))
# +0x000 = sec1 base? Actually dispatcher $a0 = &PC. struct field holding PC value = 0x11cf540 at +0x004.
# +0x000 = 0x11c3d20 = sec1 BASE. So the struct: [base, pc, ?, flags...]
# pc - base = 0xb820 = end. 
# Check field +0x008 = 0x1137980, +0x010=0x4000c, +0x014=4
