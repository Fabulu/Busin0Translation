import struct
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
exe=open(EXE,'rb').read()
VA_BASE=0xFFF80
# hook
ho=0x03CB68
print(f"hook word @ fo 0x{ho:X} = {struct.unpack_from('<I',exe,ho)[0]:08X} (expect AE20001C)")
print(f"delay slot @ 0x{ho+4:X} = {struct.unpack_from('<I',exe,ho+4)[0]:08X} (expect 00000000)")
print(f"return tgt @ 0x{ho+8:X} = {struct.unpack_from('<I',exe,ho+8)[0]:08X} (the lq, preserved)")
# j 0x4C7860 encoding
jw=(0x02<<26)|((0x4C7860>>2)&0x03FFFFFF)
print(f"replacement j 0x4C7860 = {jw:08X} (claim 0x08131E18)")
# cave region clean?
co=0x3C78E0
region=exe[co:co+128]
nz=[i for i,b in enumerate(region) if b!=0]
print(f"cave fo 0x{co:X}..+128: nonzero offsets = {nz[:10]}{'...' if len(nz)>10 else ''} (expect none / empty)")
# check the 92-byte used range specifically
used=exe[co:co+92]
print(f"cave used [0,92) all-zero: {all(b==0 for b in used)}")
# decode the proposed cave words and round-trip the key targets:
exec(open(r"C:\programmieren\wizardrytranslation\build\_recon_2f2490\dec.py").read().split("start=0x2F2490")[0])
words=[0xAE20001C,0x8F849DCC,0x10800012,0x00000000,0x8C820000,0x3C03011C,0x34633D20,
0x1443000D,0x00000000,0x27BDFFE0,0xAFBF0010,0xAFA40014,0x0C0BC6C4,0x00000000,
0x8FA40014,0x0C0BCCCC,0x00000000,0x8FBF0010,0x27BD0020,0x0804F2BC,0x00000000,0x0804F2BC,0x00000000]
va=0x4C7860
for w in words:
    print(f"  {va:08X}  {w:08X}  {dec(w,va)}")
    va+=4
