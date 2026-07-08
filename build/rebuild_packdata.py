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
    patched = 0

    # Patch R2100 in header (sectors 17-84, 68 sectors = 139,264 bytes)
    r2100_path = 'build/packdata_resources/2100_type04.raw'
    if os.path.exists(r2100_path):
        r2100_data = open(r2100_path, 'rb').read()
        assert len(r2100_data) <= 68 * SECTOR, f'R2100 too large: {len(r2100_data)} > {68*SECTOR}'
        r2100_data += b'\x00' * (68 * SECTOR - len(r2100_data))
        out.seek(17 * SECTOR)
        out.write(r2100_data)
        patched += 1
        print(f'  Patched R2100 in header ({len(r2100_data)} bytes)')

    # Patch R1370 in header (sectors 85-124, 40 sectors = 81,920 bytes)
    r1370_path = 'build/packdata_resources/1370_type04.raw'
    if os.path.exists(r1370_path):
        r1370_data = open(r1370_path, 'rb').read()
        assert len(r1370_data) <= 40 * SECTOR, f'R1370 too large: {len(r1370_data)} > {40*SECTOR}'
        r1370_data += b'\x00' * (40 * SECTOR - len(r1370_data))
        out.seek(85 * SECTOR)
        out.write(r1370_data)
        patched += 1
        print(f'  Patched R1370 in header ({len(r1370_data)} bytes)')

    cs = 125
    ntoc = []

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
            if not cc:
                # Shipping a zeroed resource silently is how a whole subsystem
                # vanishes with a green build (master-audit finding #9).
                raise SystemExit(
                    f'FATAL: resource {idx:04d} (type {tc:02d}) has no override '
                    f'AND no pristine raw -- refusing to ship a zeroed sector. '
                    f'Re-run the extraction or fix the manifest.')
            print(f'  WARN R{idx:04d}: manifest type {tc:02d} raw not found, using '
                  f'{os.path.basename(cc[0])} (type-code drift?)')
            d = open(cc[0], 'rb').read()

        # R1188 PRISTINE GATE (BUG-3): R1188 is the LIVE dialogue/narration font
        # and MUST ship byte-identical to the pristine extracted raw. The old
        # patch_r1188_* patchers corrupt ~150 live glyph cells (r/y/V artifacts).
        # If ANY override leaks in (a stale build/packdata_resources/1188_*.raw,
        # or a re-enabled patcher), fail the build LOUDLY here rather than ship a
        # corrupt dialogue font. Compare against the pristine raw (the FINAL word
        # on what R1188 must be); padding to a sector is allowed.
        if idx == 1188:
            _prist = open('extracted/packdata_raw/1188_type01.raw', 'rb').read()
            if d[:len(_prist)] != _prist or any(b != 0 for b in d[len(_prist):]):
                raise SystemExit(
                    'FATAL: R1188 is NOT pristine before PACKDATA rebuild -- a '
                    'stale override or re-enabled patch_r1188_* corrupted the '
                    'live dialogue font (BUG-3). Source: %s. Remove the override '
                    'and keep the R1188 patchers DISABLED.'
                    % (mp if os.path.exists(mp) else rp)
                )

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
