import struct,sys
sys.path.insert(0,'build/_recon_2f2490'); from dec import dec
exe=open('build/SLPM_653.78_patched','rb').read()
VA=0xFFF80
def w(va): return struct.unpack_from('<I',exe,va-VA)[0]
print("=== Hook sites (patched) ===")
print("0x308040:", hex(w(0x308040)), "(expect j 0x4D6600 = 0x08135980)")
print("0x308044:", hex(w(0x308044)), "(expect nop)")
print("0x308018:", hex(w(0x308018)), "(expect j 0x4D6660 = 0x08135998)")
print("0x307FBC:", hex(w(0x307FBC)), "(expect j 0x4D66A0 = 0x081359A8)")
print("0x307FC0:", hex(w(0x307FC0)), "(expect nop)")
print()
print("=== CAVE1 0x4D6600 (gate+advance) ===")
for i in range(17): a=0x4D6600+i*4; print(f"  {a:08X}: {dec(w(a),a)}")
print("=== CAVE3 0x4D66A0 (gate+sum-center) head ===")
for i in range(7): a=0x4D66A0+i*4; print(f"  {a:08X}: {dec(w(a),a)}")
# collision check: cave3 end vs next cave
print("\ncave3 ends 0x%X; pad ends 0x4D67A0"%(0x4D66A0+30*4))
