import struct
data=open("extracted/SLPM_653.78","rb").read()
# ELF header
assert data[:4]==b'\x7fELF', data[:4]
e_entry=struct.unpack_from("<I",data,0x18)[0]
e_phoff=struct.unpack_from("<I",data,0x1C)[0]
e_flags=struct.unpack_from("<I",data,0x24)[0]
e_phentsize=struct.unpack_from("<H",data,0x2A)[0]
e_phnum=struct.unpack_from("<H",data,0x2C)[0]
print(f"entry=0x{e_entry:08X} phoff=0x{e_phoff:X} phnum={e_phnum} phentsize={e_phentsize} flags=0x{e_flags:X}")
for i in range(e_phnum):
    o=e_phoff+i*e_phentsize
    p_type,p_off,p_vaddr,p_paddr,p_filesz,p_memsz,p_flags,p_align=struct.unpack_from("<8I",data,o)
    print(f" ph{i}: type={p_type} off=0x{p_off:X} vaddr=0x{p_vaddr:08X} filesz=0x{p_filesz:X} memsz=0x{p_memsz:X}")
