import zipfile, struct, os
RD = r'C:\programmieren\wizardrytranslation\ramdumps'
def ee(n):
    return zipfile.ZipFile(os.path.join(RD, n)).read('eeMemory.bin')
A = 0x1137ac0
saves = [('NARR thefog', 'thefog.p2s'), ('NARR didyou', 'didyouevendoanything.p2s'),
         ('DIAL barkeep', 'barkeepfull.p2s'), ('DIAL nextbk', 'nextbarkeep.p2s'),
         ('DIAL verastill', 'verastillbad.p2s'), ('DIAL verafourth', 'verafourth.p2s'),
         ('REQ requestdesc', 'requestdesc.p2s'), ('REQ reqissues', 'requestdescissues.p2s'),
         ('REQ advsupp', 'advsupport.p2s')]
for label, fn in saves:
    m = ee(fn)
    bw = struct.unpack_from('<h', m, A + 0x1c)[0]
    bx = struct.unpack_from('<h', m, A + 0x3c)[0]
    w0 = struct.unpack_from('<h', m, A + 0x00)[0]
    # dump first 0x60 bytes as u32
    words = [struct.unpack_from('<I', m, A + i)[0] for i in range(0, 0x60, 4)]
    print('%-18s bw=%5d boxX=%5d w0=%d' % (label, bw, bx, w0))
    print('   ', ' '.join('%08x' % w for w in words))
