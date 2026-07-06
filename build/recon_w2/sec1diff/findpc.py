import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
print("ee size",len(ee))
# EXE at RAM 0x100000. Interpreter dispatcher VA 0x2F3230 run-loop ~0x2F3330.
# We need the interpreter's state: current script base pointer + PC.
# Strategy: locate R1197 sec1 bytes loaded in EE RAM (search for a distinctive sec1 byte pattern),
# then find PC register / state struct referencing it.
pat=open('build/patched_type2/1197_type02.raw','rb').read()
s2off=struct.unpack_from("<I",pat,0x18)[0]
sec1=pat[0x20:s2off]
# distinctive 32-byte signature from middle of sec1
import re
sig=sec1[0x1000:0x1020]
idx=ee.find(sig)
print("sec1 sig found in EE at:",hex(idx) if idx>=0 else "NOT FOUND")
# find ALL occurrences
occ=[]
start=0
while True:
    i=ee.find(sig,start)
    if i<0:break
    occ.append(i);start=i+1
print("occurrences:",[hex(o) for o in occ])
# the base of sec1 in RAM = occ - 0x1000
for o in occ:
    base=o-0x1000
    print("candidate sec1 base in RAM:",hex(base))
