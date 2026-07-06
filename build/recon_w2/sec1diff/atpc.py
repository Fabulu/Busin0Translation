import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
# PC = 0x11cf540. Read the FULL loaded resource in RAM (sec1+sec2 contiguous?).
# In RAM the resource is loaded as one blob. sec2 follows sec1? PC=base+0xb820.
# read 16 bytes at PC from RAM:
pc=0x11cf540
print("bytes at PC (RAM):",ee[pc:pc+16].hex())
opc=(ee[pc]<<8)|ee[pc+1]
print("opcode read at PC: 0x%04x len=%s"%(opc, S.LENB.get(opc,'INVALID(>=193 -> dispatcher error path)')))
# Is this >=193? then dispatcher hits the 'else' debug branch and RETURNS 1 -> run loop sees v1=1...
# Actually dispatcher: opcode>=0xc1 -> debug print, mp=0, return... let's check run loop reaction.
# In RAM, what is loaded right after sec1? It should be the resource's sec2 (English text).
# The v96 sec2 head:
print("RAM sec2 head (=v96 build):",ee[base+0xb840:base+0xb840+16].hex())
# But PC=base+0xb820 = 0x20 BEFORE sec2_off 0xb840. So PC is in the LAST 0x20 bytes of sec1.
print("RAM sec1[0xb800:0xb840]:",ee[base+0xb800:base+0xb840].hex())
