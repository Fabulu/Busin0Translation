import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee = open('build/recon_portrait4/extract/request__ee.bin','rb').read()

def hexdump(addr, n=64):
    b = ee[addr:addr+n]
    return ' '.join(f'{x:02x}' for x in b)

for a in (0x5601F2, 0xDC1AF2):
    print(f'\n=== RAM 0x{a:X} ===')
    print('  -16 .. +48:')
    print('   ', hexdump(a-16, 64))
    # interpret as BE u16 run
    words = struct.unpack_from('>32H', ee, a)
    print('  BE u16:', ' '.join(f'{w:04x}' for w in words))
    words_le = struct.unpack_from('<32H', ee, a)
    print('  LE u16:', ' '.join(f'{w:04x}' for w in words_le))
