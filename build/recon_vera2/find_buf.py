import sys
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()
# The directory entries: each 16 bytes: idx(u32), size(u32=0x130), offset(u32), pad
# 0xDC1000: idx=0x10, size=0x130, off=0x1440
# offset 0x1440 from buffer base -> name record? 0xDC1042-0x1440 = base?
# Actually record0 name at 0xDC1042. dir entry idx0x10 off=0x1440.
# Let's find buffer base by scanning backward for dir entry idx=0
p=0xDC1000
# walk backward in 16-byte steps while pattern looks like dir (size=0x130)
base=p
while base>=16:
    idx=int.from_bytes(ram[base-16:base-12],'little')
    size=int.from_bytes(ram[base-12:base-8],'little')
    if size==0x130:
        base-=16
    else:
        break
print(f"dir start ~0x{base:X}")
# dump first entries
for i in range(20):
    off=base+i*16
    idx=int.from_bytes(ram[off:off+4],'little')
    size=int.from_bytes(ram[off+4:off+8],'little')
    rel=int.from_bytes(ram[off+8:off+12],'little')
    print(f"  entry{i}: idx={idx} size=0x{size:X} rel=0x{rel:X}")
