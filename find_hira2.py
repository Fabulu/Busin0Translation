import zipfile, struct
def read_ee_ram(p):
    with zipfile.ZipFile(p, 'r') as z:
        with z.open('eeMemory.bin') as f:
            return f.read()
ram = read_ee_ram('C:/Programmieren/wizardrytranslation/Nameentrystate.p2s')
off = 0x4C9AB0
print('Full katakana table 100 rows')
for row in range(100):
    vals = [struct.unpack_from('<H', ram, off+row*12+c*2)[0] for c in range(6)]
    print(f'Row {row:3d}: {vals}')
print('Searching stride-57 patterns')
for addr in range(0x100000, 0x2000000, 2):
    v0 = struct.unpack_from('<H', ram, addr)[0]
    if v0 == 0 or v0 > 800: continue
    v1 = struct.unpack_from('<H', ram, addr+2)[0]
    if v1 - v0 != 57: continue
    v2 = struct.unpack_from('<H', ram, addr+4)[0]
    if v2 - v1 != 57: continue
    v3 = struct.unpack_from('<H', ram, addr+6)[0]
    if v3 - v2 != 57: continue
    v4 = struct.unpack_from('<H', ram, addr+8)[0]
    if v4 - v3 != 57: continue
    v5 = struct.unpack_from('<H', ram, addr+10)[0]
    if v5 - v4 != 57: continue
    n0 = struct.unpack_from('<H', ram, addr+12)[0]
    if n0 == v0 + 1:
        print(f'MATCH 0x{addr:08X}: [{v0},{v1},{v2},{v3},{v4},{v5}]')
        for row in range(15):
            vals = [struct.unpack_from('<H', ram, addr+row*12+c*2)[0] for c in range(6)]
            print(f'  Row {row}: {vals}')
print('Done.')
