import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
exe = r'C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78'
with open(exe, 'rb') as f:
    e = f.read()
phoff = struct.unpack_from('<I', e, 0x1C)[0]
phsz = struct.unpack_from('<H', e, 0x2A)[0]
phnum = struct.unpack_from('<H', e, 0x2C)[0]
print('PH: off=0x%X sz=%d n=%d' % (phoff, phsz, phnum))
for i in range(phnum):
    o = phoff + i * phsz
    pt = struct.unpack_from('<I', e, o)[0]
    po = struct.unpack_from('<I', e, o+4)[0]
    pv = struct.unpack_from('<I', e, o+8)[0]
    pf = struct.unpack_from('<I', e, o+16)[0]
    pm = struct.unpack_from('<I', e, o+20)[0]
    print('  [%d] t=%d off=0x%X va=0x%08X fs=0x%X ms=0x%X' % (i,pt,po,pv,pf,pm))
    if pt == 1 and pv <= 0x4C9D20 < pv + pf:
        fo = po + (0x4C9D20 - pv)
        print('  -> 0x4C9D20 at file 0x%X' % fo)
        d = e[fo:fo+40]
        for j in range(10):
            v = struct.unpack_from('<I', d, j*4)[0]
            x = 'FFFF' if v==0xFFFFFFFF else '0x%08X'%v
            print('    [%d] %s' % (j, x))
print('Done.')
