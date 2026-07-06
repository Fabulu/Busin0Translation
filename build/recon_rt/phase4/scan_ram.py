import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
print('EE size', len(ee))
# Find a distinctive injected R1197 string in RAM to confirm our build is loaded.
# 'Requests' selection / Gin. Find the encoded glyph stream for a known english string.
# Easier: search for marker pattern FFC0 ... FFC1 (BE) in RAM near english glyphs.
# First confirm trampoline present (v94): EXE loaded at 0x100000, patch at 0x1F25E8 JAL 0x4B0DD0
# JAL encoding: 0x0C target>>2. target 0x4B0DD0 -> 0x0C12C374 ... let's just check bytes
off=0x1F25E8
instr=struct.unpack_from('<I',ee,off)[0]
print('instr@VA0x1F25E8 = %08X'%instr)
op=instr>>26; tgt=(instr&0x3FFFFFF)<<2
print('  opcode=%d (3=JAL) jal_target=0x%08X'%(op,tgt))
# trampoline body at 0x4B0DD0
tramp=ee[0x4B0DD0:0x4B0DD0+32]
print('  trampoline bytes:', tramp.hex())
