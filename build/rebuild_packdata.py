import struct, json, os, math

os.chdir('C:/Programmieren/wizardrytranslation')

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
n_entries = len(manifest)
SECTOR = 2048

with open('extracted/PACKDATA.DIG', 'rb') as f:
    otoc = [struct.unpack('<III', f.read(12)) for _ in range(n_entries)]
    f.seek(0)
    hdr = f.read(125 * SECTOR)

orig_size = os.path.getsize('extracted/PACKDATA.DIG')

with open('build/PACKDATA_v3.DIG', 'wb') as out:
    out.write(hdr)
    cs = 125
    ntoc = []
    patched = 0

    for entry in manifest:
        idx = entry['index']
        if entry.get('skipped'):
            ntoc.append(otoc[idx])
            continue

        tc = entry['type_code']
        fn = f'{idx:04d}_type{tc:02d}.raw'
        mp = f'build/packdata_resources/{fn}'
        rp = f'extracted/packdata_raw/{fn}'

        if os.path.exists(mp):
            d = open(mp, 'rb').read()
            patched += 1
        elif os.path.exists(rp):
            d = open(rp, 'rb').read()
        else:
            import glob
            cc = glob.glob(f'extracted/packdata_raw/{idx:04d}_type*.raw')
            d = open(cc[0], 'rb').read() if cc else b'\x00' * SECTOR

        sc = math.ceil(len(d) / SECTOR)
        if len(d) < sc * SECTOR:
            d += b'\x00' * (sc * SECTOR - len(d))

        out.seek(cs * SECTOR)
        out.write(d)
        ntoc.append((cs, sc, tc))
        cs += sc

    out.seek(0)
    for so, sc, tc in ntoc:
        out.write(struct.pack('<III', so, sc, tc))

    out.seek(0, 2)
    fs = out.tell()

print(f'Patched: {patched} resources')
print(f'Size: {fs:,} bytes (orig: {orig_size:,}, diff: {fs - orig_size:+,})')

if fs < orig_size:
    with open('build/PACKDATA_v3.DIG', 'ab') as f:
        f.write(b'\x00' * (orig_size - fs))
    print(f'Padded to {orig_size:,} bytes')
elif fs > orig_size:
    print(f'WARNING: {fs - orig_size:,} bytes LARGER than original!')
