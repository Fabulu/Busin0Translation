import zipfile, struct, os, glob
RD = r'C:\programmieren\wizardrytranslation\ramdumps'
RAW = r'C:\programmieren\wizardrytranslation\extracted\packdata_raw'
def ee(n):
    return zipfile.ZipFile(os.path.join(RD, n)).read('eeMemory.bin')

# For each loaded sec1 base, grab 256 bytes and find which raw type02 sec1 matches
def fingerprint(m, base):
    return bytes(m[base:base+256])

# Build raw sec1 index: res -> sec1[0:256]
rawidx = {}
for p in sorted(glob.glob(os.path.join(RAW, '*_type02.raw'))):
    res = int(os.path.basename(p)[:4])
    raw = open(p, 'rb').read()
    try:
        sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
        sec1 = raw[0x20:sec2_off]
        rawidx[res] = sec1
    except Exception:
        pass

for label, fn, base in [('NARR', 'thefog.p2s', 0x011c9060),
                        ('DIAL/REQ', 'barkeepfull.p2s', 0x011c3d20)]:
    m = ee(fn)
    fp = fingerprint(m, base)
    best = None
    for res, sec1 in rawidx.items():
        if len(sec1) >= 256 and sec1[:256] == fp:
            best = res
            break
    print('%-10s base=%08x -> R%s (exact256)' % (label, base, best))
    # also report next chunk
    if best is None:
        # fuzzy: longest matching prefix
        bestlen = 0; bestres = None
        for res, sec1 in rawidx.items():
            n = min(len(sec1), 2048)
            k = 0
            while k < n and k < len(fp)*8 and sec1[k] == m[base+k]:
                k += 1
            # compare 2048
            L = 0
            for j in range(min(len(sec1), 4096)):
                if base+j < len(m) and sec1[j] == m[base+j]:
                    L += 1
                else:
                    break
            if L > bestlen:
                bestlen = L; bestres = res
        print('   fuzzy best R%s prefix-match %d bytes' % (bestres, bestlen))
