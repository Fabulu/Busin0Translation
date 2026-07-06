import struct
exe=open(r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78",'rb').read()
def chk(name,fo,nwords):
    region=exe[fo:fo+nwords*4]
    allzero=all(b==0 for b in region)
    print(f"{name} file 0x{fo:X} ({nwords}w/{nwords*4}B): {'ZERO/free' if allzero else 'NONZERO: '+region[:16].hex()}")
# cave1 12 words, cave2 11 words, cave3 18 words (with gate added)
chk("cave1 @0x4D6600", 0x3D6680, 16)
chk("cave2 @0x4D6660", 0x3D66E0, 16)
chk("cave3 @0x4D66A0", 0x3D6720, 24)
# check the whole pad run
chk("pad run", 0x3D6680, 0x40)
# confirm hook sites in pristine
def va(addr): return struct.unpack_from('<I',exe,addr-0xFFF80)[0]
print("\nHook sites (pristine):")
print("0x308040 =", hex(va(0x308040)), "(expect 0x24420018 addiu v0,v0,0x18)")
print("0x308044 =", hex(va(0x308044)), "(expect 0xA7A201CC sh v0,0x1cc(sp))")
print("0x308018 =", hex(va(0x308018)), "(expect 0x87A301CC lh v1,0x1cc(sp))")
print("0x30801C =", hex(va(0x30801C)), "(expect move a0,s5)")
print("0x307FBC =", hex(va(0x307FBC)), "(expect 0x00052040 sll a0,a1,1)")
print("0x307FC0 =", hex(va(0x307FC0)), "(expect 0x00852021 addu a0,a0,a1)")
