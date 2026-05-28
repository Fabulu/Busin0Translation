import zipfile, os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
O = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
HIRA = r'C:\Programmieren\wizardrytranslation\NameEntryHiraganamode.p2s'
if not os.path.exists(HIRA):
    print('No hiragana save state')
    exit()
with zipfile.ZipFile(HIRA, 'r') as z:
    z.extract('eeMemory.bin', os.path.join(O, 'hira'))
with open(os.path.join(O, 'hira', 'eeMemory.bin'), 'rb') as f:
    hram = f.read()
with open(os.path.join(O, 'eeMemory.bin'), 'rb') as f:
    kram = f.read()
same_kt = kram[0x4C9D20:0x4CA600] == hram[0x4C9D20:0x4CA600]
same_ne = kram[0x4C99B0:0x4C9CE0] == hram[0x4C99B0:0x4C9CE0]
print('Kanji table same: %s' % same_kt)
print('Name entry same: %s' % same_ne)
if not same_ne:
    diffs = 0
    for offset in range(0x4C99B0, 0x4C9CE0, 12):
        k6 = [struct.unpack_from('<H', kram, offset+j*2)[0] for j in range(6)]
        h6 = [struct.unpack_from('<H', hram, offset+j*2)[0] for j in range(6)]
        if k6 != h6:
            diffs += 1
            if diffs <= 20:
                ks = ' '.join(['%04X'%v for v in k6])
                hs = ' '.join(['%04X'%v for v in h6])
                print('  DIFF 0x%08X: K=%s H=%s' % (offset, ks, hs))
    print('Total diffs: %d' % diffs)
print('')
print('Done.')
