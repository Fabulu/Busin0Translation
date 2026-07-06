import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()

# Does the R2654 sub8 (which contains the katakana run at file 0x8a4c) get loaded into RAM?
# Search RAM for the run preceding it: 0x3e 04a7 04aa 0121 ... (file 0x8a30 area)
# That's a distinctive sub8 fingerprint. Search for sub8 marker bytes.
fp = bytes([0x04,0xa7,0x04,0xaa,0x01,0x21,0x00,0x85])  # BE u16 04a7 04aa 0121 0085
i=ee.find(fp)
print('sub8 fingerprint (04a7 04aa 0121 0085) in RAM:', hex(i) if i>=0 else 'NOT FOUND')

fp33 = bytes([0x02,0x91,0x00,0x97,0x00,0xab,0x02,0xc5])  # sub33 fingerprint near 0x34aa4
i=ee.find(fp33)
print('sub33 fingerprint in RAM:', hex(i) if i>=0 else 'NOT FOUND')

# The romanized sub7 Vera (BE u16 0095 00a4 00b1 00a0) -- is it loaded in RAM?
ver_rom_be = bytes([0x00,0x95,0x00,0xa4,0x00,0xb1,0x00,0xa0])
ver_rom_le = bytes([0x95,0x00,0xa4,0x00,0xb1,0x00,0xa0,0x00])
for nm,n in [('romanized BE',ver_rom_be),('romanized LE',ver_rom_le)]:
    i=ee.find(n); occ=[]
    while i!=-1 and len(occ)<10:
        occ.append(i); i=ee.find(n,i+1)
    print(f'sub7 romanized Vera ({nm}) in RAM: {[hex(x) for x in occ]}')

# context dump around the two katakana RAM hits — wider, to see struct
for a in (0x5601F2, 0xDC1AF2):
    print(f'\n=== wide context RAM 0x{a:X} (-64..+96) ===')
    for o in range(a-64, a+96, 16):
        b=ee[o:o+16]
        print(f'  0x{o:08x}: '+' '.join(f'{x:02x}' for x in b))
