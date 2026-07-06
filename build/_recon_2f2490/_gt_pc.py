import zipfile, struct, os, glob
RD = r'C:\programmieren\wizardrytranslation\ramdumps'
RAW = r'C:\programmieren\wizardrytranslation\extracted\packdata_raw'
def ee(n):
    return zipfile.ZipFile(os.path.join(RD, n)).read('eeMemory.bin')
SEC1G = 0x564ED0

def res_sec1len(res):
    raw = open(os.path.join(RAW, '%04d_type02.raw' % res), 'rb').read()
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    return sec2_off - 0x20

saves = [('NARR thefog R1196', 'thefog.p2s', 1196),
         ('NARR didyou R1196', 'didyouevendoanything.p2s', 1196),
         ('DIAL barkeep R1197', 'barkeepfull.p2s', 1197),
         ('DIAL nextbk R1197', 'nextbarkeep.p2s', 1197),
         ('DIAL verastill R1197', 'verastillbad.p2s', 1197),
         ('DIAL verafourth R1197', 'verafourth.p2s', 1197),
         ('REQ requestdesc R1197', 'requestdesc.p2s', 1197),
         ('REQ advsupp R1197', 'advsupport.p2s', 1197)]
for label, fn, res in saves:
    m = ee(fn)
    s1 = struct.unpack_from('<I', m, SEC1G)[0]
    slen = res_sec1len(res)
    lo, hi = s1, s1 + slen
    # find pointers into the sec1 range (the live PC / ctx pc field)
    ptrs = []
    for a in range(0x100000, 0x1300000, 4):
        v = struct.unpack_from('<I', m, a)[0]
        if lo <= v < hi:
            ptrs.append((a, v - s1))
    print('%-22s sec1=%08x len=%d  #ptrs-into-sec1=%d' % (label, s1, slen, len(ptrs)))
    # show a few unique target offsets
    offs = sorted(set(o for _, o in ptrs))
    print('   distinct sec1 offsets targeted (first 25):', offs[:25])
