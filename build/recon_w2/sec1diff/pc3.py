import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
pc_ram=0x11cf540
pcoff=pc_ram-base
print("PC candidate sec1-relative offset = 0x%x (sec1 len 0xb820=47136)"%pcoff)
sec1_ram=ee[base:base+47136]
ok,instrs=S.walk(sec1_ram)
print("walk ok",ok,"is pcoff an instr boundary:",pcoff in instrs)
if pcoff in instrs: print("opcode at PC:",hex(instrs[pcoff]))
# dump bytes around PC
print("bytes @PC:", sec1_ram[pcoff:pcoff+32].hex())
# Show the full state struct at 0x564ed0
print("\nstate struct @0x564ed0:")
for k in range(-8,24):
    v=struct.unpack_from("<I",ee,0x564ed0+k*4)[0]
    print("  +0x%03x: 0x%08x"%(k*4 & 0xffffffff if k>=0 else (k*4), v))
