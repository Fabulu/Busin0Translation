import zipfile, struct, os
RD = r'C:\programmieren\wizardrytranslation\ramdumps'
def ee(n):
    return zipfile.ZipFile(os.path.join(RD, n)).read('eeMemory.bin')
addrs = [0x159e9c, 0x15ef24, 0x17bf94]
saves = [('NARR thefog', 'thefog.p2s'), ('NARR didyou', 'didyouevendoanything.p2s'),
         ('DIAL barkeep', 'barkeepfull.p2s'), ('DIAL nextbk', 'nextbarkeep.p2s'),
         ('DIAL verastill', 'verastillbad.p2s'), ('DIAL verafourth', 'verafourth.p2s'),
         ('REQ requestdesc', 'requestdesc.p2s'), ('REQ reqissues', 'requestdescissues.p2s'),
         ('REQ advsupp', 'advsupport.p2s')]
for label, fn in saves:
    m = ee(fn)
    print('===', label)
    for a in addrs:
        bw = struct.unpack_from('<h', m, a + 0x1c)[0]
        bx = struct.unpack_from('<h', m, a + 0x3c)[0]
        lc0 = struct.unpack_from('<h', m, a + 0x00)[0]
        print('  @%x bw=%d boxX=%d w0=%d' % (a, bw, bx, lc0))
