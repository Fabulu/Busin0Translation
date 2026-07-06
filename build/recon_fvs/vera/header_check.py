import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
d=open('extracted/packdata_raw/1892_type20.raw','rb').read()
# type20 container? check header
print('first 0x40 bytes:')
for i in range(0,0x40,16):
    print(f'  +{i:03x}:', ' '.join(f'{x:02x}' for x in d[i:i+16]))
# is 0x270 the first record or is there a record at 0x140?
print('\nLE u16 0x0..0x270 nonzero:')
for o in range(0,0x270,2):
    w=struct.unpack_from('<H',d,o)[0]
    if w: print(f'  0x{o:04x}: {w:04x} ({w})')
