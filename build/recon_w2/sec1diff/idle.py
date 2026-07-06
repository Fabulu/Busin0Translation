import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
# The dispatcher reads opcode at PC. If PC=0x11cf540 reads 0x0034 (op 52).
# 0x11cf540 = base+0xb820. base=0x11c3d20. Confirm what's at PC: in RAM, sec2 starts at base+0xb840.
# So PC=base+0xb820 is 0x20 bytes BEFORE sec2 = still sec1, which is NOPs (zeros).
# Earlier confusion: ee[base+0xb820:] showed text. Let me re-read precisely.
base=0x11c3d20
print("base+0xb800:",ee[base+0xb800:base+0xb810].hex())
print("base+0xb810:",ee[base+0xb810:base+0xb820].hex())
print("base+0xb820 (PC):",ee[base+0xb820:base+0xb830].hex())
print("base+0xb830:",ee[base+0xb830:base+0xb840].hex())
print("base+0xb840 (sec2_off):",ee[base+0xb840:base+0xb850].hex())
# So is PC reading zeros (NOP, idle) or text?
