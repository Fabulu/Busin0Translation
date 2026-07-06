import struct
ee=open('_q7/chargen_ee.bin','rb').read()
# gp register: gp-0x62d8 == 0x4FED18 => gp = 0x4FED18 + 0x62d8 = 0x504FF0
gp=0x4FED18 + 0x62d8
print("gp =", hex(gp))
# verify resident ADV table presence at 0x4C7564 (must equal LUT)
print("ADV[' '] (idx0) =", ee[0x4C7564], "(expect 9)")
print("ADV['M'-32=0x2D] =", ee[0x4C7564+0x2D], "(expect 23)")
# Patch14 resident: confirm table at 0x4C7564 is loaded (it's in EXE rodata, same in RAM)
# screen-mode value
print("gp-0x62d8 [0x4FED18] =", hex(struct.unpack_from('<I',ee,0x4FED18)[0]))
# Patch 14 hook check: VA 0x3097A0 file? in RAM at 0x3097A0
print("0x3097A0 word =", hex(struct.unpack_from('<I',ee,0x3097A0)[0]))
