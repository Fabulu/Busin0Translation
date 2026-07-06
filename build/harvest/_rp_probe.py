import struct
ee="C:/programmieren/wizardrytranslation/build/harvest/_requestperfect/eeMemory.bin"
d=open(ee,"rb").read()
def w(va): return struct.unpack_from("<I",d,va)[0]  # EE RAM: VA==file offset
print("=== Provenance / patch presence (live VA == offset) ===")
checks=[
 ("0x308CB0 P22 adv +18 (want 0x24420012)",0x308CB0),
 ("0x308D7C P22 adv sibling (want 0x24420012)",0x308D7C),
 ("0x30896C P22 reserve head (want 0x000410C0)",0x30896C),
 ("0x308974 P22 reserve tail (want 0x00021040)",0x308974),
 ("0x308328 P23 li a0,8 (want 0x24040008)",0x308328),
 ("0x30973C P24 j cave (want 0x08132A8C or similar)",0x30973C),
 ("0x308CAC P25 hook (pristine 0x87A201CE, j if installed)",0x308CAC),
 ("0x3097A0 P14 marker (want 0x08131D50)",0x3097A0),
 ("0x308040 P19/diag hook",0x308040),
 ("0x3079DC int mono stride (pristine 0x24420018 / edited 0x24420012)",0x3079DC),
 ("0x3076FC float pitch const (pristine 0x3442C28F / edited 0x344251EC)",0x3076FC),
]
for nm,va in checks:
    print(f"  {nm}: 0x{w(va):08X}")
# screen-mode global gp-0x62d8 = 0x4FED18
print("=== mode global 0x4FED18 ===", "0x%08X"%w(0x4FED18))
