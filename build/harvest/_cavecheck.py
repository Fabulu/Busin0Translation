import struct
# Check P24 cave extent vs P25 cave start in pristine EXE (should both be zero-pad)
exe=open("C:/programmieren/wizardrytranslation/extracted/SLPM_653.78","rb").read()
def fo(va): return va-0x100000+0x80
print("=== zero check 0x4CAA30..0x4CAB00 (P24 cave 0x4CAA30, P25 cave 0x4CAA48) ===")
for va in range(0x4CAA00,0x4CAB00,4):
    w=struct.unpack_from("<I",exe,fo(va))[0]
    mark=""
    if va==0x4CAA30: mark=" <-P24 cave start"
    if va==0x4CAA48: mark=" <-P25 cave start"
    if w!=0: print(f"  0x{va:06X}: {w:08X}{mark}")
    elif mark: print(f"  0x{va:06X}: 00000000{mark}")
# P24 cave length: read patch_exe P24 cave words count
