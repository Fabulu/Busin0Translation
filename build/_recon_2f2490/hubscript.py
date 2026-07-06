import struct,sys
ee=open(sys.argv[1],'rb').read()
base=0x011C3D20
# opcode table to know byte lengths is in EXE; here just dump raw and the opcodes
data=ee[base:base+0x400]
print("hub script bytes @0x011C3D20 (first 0x400):")
# print as big-endian u16 stream with opcode annotation hint
i=0
while i < 0x120:
    b=data[i:i+16]
    hexs=' '.join(f'{x:02X}' for x in b)
    print(f"+{i:04X}: {hexs}")
    i+=16
