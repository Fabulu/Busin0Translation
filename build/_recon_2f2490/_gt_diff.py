import zipfile, struct, os
RD = r'C:\programmieren\wizardrytranslation\ramdumps'
def ee(n):
    return zipfile.ZipFile(os.path.join(RD, n)).read('eeMemory.bin')

# screen-mode global per CLAUDE notes
narr = ee('thefog.p2s')
dial = ee('barkeepfull.p2s')
req = ee('requestdesc.p2s')
print('screen-mode 0x4FED18:',
      struct.unpack_from('<I', narr, 0x4FED18)[0],
      struct.unpack_from('<I', dial, 0x4FED18)[0],
      struct.unpack_from('<I', req, 0x4FED18)[0])

# scan for a descriptor: narration boxX==0 bw==313, dialogue boxX==-1 bw==0
# Look anywhere boxX(+0x3c)==-1 in dialogue
N = len(narr)
hits = 0
for a in range(0x100000, 0x2000000, 4):
    if a + 0x40 > N:
        break
    nbw = struct.unpack_from('<h', narr, a + 0x1c)[0]
    nbx = struct.unpack_from('<h', narr, a + 0x3c)[0]
    dbw = struct.unpack_from('<h', dial, a + 0x1c)[0]
    dbx = struct.unpack_from('<h', dial, a + 0x3c)[0]
    if nbw == 313 and nbx == 0 and dbx == -1 and dbw == 0:
        print('CANDIDATE @%x  narr(bw=%d,bx=%d) dial(bw=%d,bx=%d)' % (a, nbw, nbx, dbw, dbx))
        hits += 1
        if hits > 30:
            break
print('candidates:', hits)
