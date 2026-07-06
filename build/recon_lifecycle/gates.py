import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def by(m,va): return m[va]
def w32(m,va): return struct.unpack('<I',m[va:va+4])[0]
GP=0x504FF0
gates=[
 (GP-26948,'0x4FE684 (2F1590 gate)','b'),
 (GP-26980,'0x4FE664 (2F15A0 gate)','b'),
 (GP-29492,'0x4FE53C (131D20 pause gate)','b'),
 (GP-29480,'0x4FE548','b'),
 (GP-29484,'0x4FE544','b'),
 (GP-29488,'0x4FE540','b'),
 (GP-26956,'0x4FE678 (input bitmask)','w'),
 (GP-26944,'0x4FE6B0 (gp-26944)','b'),
 (GP-26940,'0x4FE6B4 (gp-26940)','b'),
]
W=load('C:/programmieren/wizardrytranslation/ramdumps/tavern104.p2s')
F=load('C:/programmieren/wizardrytranslation/ramdumps/fuckinghellman.p2s')
print(f'{"name":40} {"WORKING":>12} {"FROZEN":>12}  DIFF')
for va,nm,sz in gates:
    wv=by(W,va) if sz=='b' else w32(W,va)
    fv=by(F,va) if sz=='b' else w32(F,va)
    d='  <<<<< DIFF' if wv!=fv else ''
    print(f'{nm:40} {wv:>12} {fv:>12}{d}')
