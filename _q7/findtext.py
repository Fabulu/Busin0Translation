import struct
ee=open('_q7/chargen_ee.bin','rb').read()
# Search for "Miser" / "Lives" in multiple encodings.
targets=[b'Miser', b'Lives', b'Simple', b'hoard']
for t in targets:
    # ascii
    i=ee.find(t)
    print(t, "ascii at", hex(i) if i>=0 else "none")
    # as u16 LE high-byte cells: each char c -> bytes [00, c]
    pat_hi=b''.join(bytes([0x00, c]) for c in t)
    i=ee.find(pat_hi); print(t, "u16 hi-byte(00 c) at", hex(i) if i>=0 else "none")
    # as u16 LE low-byte cells: each char c -> bytes [c, 00]
    pat_lo=b''.join(bytes([c, 0x00]) for c in t)
    i=ee.find(pat_lo); print(t, "u16 lo-byte(c 00) at", hex(i) if i>=0 else "none")
    # char-32 high byte: bytes [00, c-32]
    pat_h32=b''.join(bytes([0x00, c-32]) for c in t)
    i=ee.find(pat_h32); print(t, "u16 (00,c-32) at", hex(i) if i>=0 else "none")
    # char-32 low byte: bytes [c-32, 00]
    pat_l32=b''.join(bytes([c-32, 0x00]) for c in t)
    i=ee.find(pat_l32); print(t, "u16 (c-32,00) at", hex(i) if i>=0 else "none")
    print()
