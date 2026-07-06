import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
# The Japanese ISO contains PACKDATA.DIG as a file. We need its offset in the ISO.
# Simpler: search the ISO for the exact R1197 header signature and surrounding sec1.
iso=open(r"C:/programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso","rb")
# R1197 header starts: 00000000 1fb80000 20000000 00000000 01000000 5c0e0100 40b80000
sig=bytes.fromhex("000000001fb800002000000000000000010000005c0e010040b80000")
data=iso.read()  # 1.27GB - read fully (we have memory)
idx=data.find(sig)
print("R1197 header found in JP ISO at:", hex(idx) if idx>=0 else "NOT FOUND")
if idx>=0:
    b=data[idx:idx+0x20000]
    sec1=b[0x20:0x20+0x1FB8]
    tgt=struct.unpack_from(">I",sec1,0x5D0+10)[0]
    c=struct.unpack_from(">H",sec1,0x117E+4)[0]
    print("JP ISO R1197: 0x06@5D0 target=0x%04X  0Cidx=0x%02X"%(tgt,c))
