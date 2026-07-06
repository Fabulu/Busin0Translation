import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
d=open('extracted/SLPM_653.78','rb').read()
e_entry=struct.unpack_from('<I',d,0x18)[0]
e_phoff=struct.unpack_from('<I',d,0x1C)[0]
e_phentsize=struct.unpack_from('<H',d,0x2A)[0]
e_phnum=struct.unpack_from('<H',d,0x2C)[0]
print(f"entry=0x{e_entry:X} phoff=0x{e_phoff:X} phentsize={e_phentsize} phnum={e_phnum}")
for i in range(e_phnum):
    off=e_phoff+i*e_phentsize
    p_type,p_offset,p_vaddr,p_paddr,p_filesz,p_memsz,p_flags,p_align=struct.unpack_from('<8I',d,off)
    print(f"PH{i}: type={p_type} off=0x{p_offset:X} vaddr=0x{p_vaddr:X} filesz=0x{p_filesz:X} memsz=0x{p_memsz:X} flags={p_flags}")
