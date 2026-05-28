import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
exe = r'C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78'
with open(exe, 'rb') as f:
    e = f.read()
f1 = 0x3CAD20
d = e[f1:f1+40]
vs = [struct.unpack_from('<I', d, j)[0] for j in range(0, 40, 4)]
print('Kanji table at EXE 0x%06X:' % f1)
for i, v in enumerate(vs):
    print('  [%d] 0x%08X' % (i, v))
f2 = 0x3C17F0
d2 = e[f2:f2+20]
vs2 = [struct.unpack_from('<H', d2, j)[0] for j in range(0, 20, 2)]
print('ASCII table at EXE 0x%06X: %s' % (f2, ' '.join(['%04X'%v for v in vs2])))
f3 = 0x3CAAB0
d3 = e[f3:f3+24]
vs3 = [struct.unpack_from('<H', d3, j)[0] for j in range(0, 24, 2)]
print('Name entry at EXE 0x%06X: %s' % (f3, ' '.join(['%04X'%v for v in vs3])))
print('Done.')
