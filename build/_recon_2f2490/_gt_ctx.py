import zipfile, struct, os
RD = r'C:\programmieren\wizardrytranslation\ramdumps'
def ee(n):
    return zipfile.ZipFile(os.path.join(RD, n)).read('eeMemory.bin')
saves = [('NARR thefog', 'thefog.p2s'), ('NARR didyou', 'didyouevendoanything.p2s'),
         ('DIAL barkeep', 'barkeepfull.p2s'), ('DIAL nextbk', 'nextbarkeep.p2s'),
         ('DIAL verastill', 'verastillbad.p2s'), ('DIAL verafourth', 'verafourth.p2s'),
         ('REQ requestdesc', 'requestdesc.p2s'), ('REQ advsupp', 'advsupport.p2s')]
SEC1G = 0x564ED0
SEC2G = 0x564ED4
for label, fn in saves:
    m = ee(fn)
    s1 = struct.unpack_from('<I', m, SEC1G)[0]
    s2 = struct.unpack_from('<I', m, SEC2G)[0]
    print('%-18s sec1base=%08x sec2base=%08x' % (label, s1, s2))
