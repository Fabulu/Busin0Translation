import struct,sys
sys.path.insert(0,'build/_recon_2f2490'); from dec import dec
exe=open('build/SLPM_653.78_patched','rb').read()
VA=0xFFF80
def w(va): return struct.unpack_from('<I',exe,va-VA)[0]
print("0x308040:", hex(w(0x308040)), "(j cave1)")
print("0x308044:", hex(w(0x308044)), "(nop)")
print("0x308018:", hex(w(0x308018)), "(j cave2)")
print("0x307FBC:", hex(w(0x307FBC)), "(PRISTINE expect 0x00052040 sll a0,a1,1)")
print("0x307FC0:", hex(w(0x307FC0)), "(PRISTINE expect 0x00852021 addu a0,a0,a1)")
# cave3 region should be ZERO (not hooked)
c3=exe[0x3D6720:0x3D6720+120]
print("cave3 region all-zero:", all(b==0 for b in c3))
