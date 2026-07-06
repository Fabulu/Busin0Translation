import struct
ee=open('_q7/chargen_ee.bin','rb').read()
base=0x4C7564
print("ADV LUT @0x4C7564 (bytes):")
row=[]
for i in range(96):
    b=ee[base+i]
    ch=chr(i+32) if i+32<0x7f else '?'
    row.append(f"{ch}={b}")
print(' '.join(row[:48]))
print(' '.join(row[48:]))
# Also dump a few u16/u32 interpretations
print("\nFirst 16 bytes hex:", ee[base:base+16].hex())
