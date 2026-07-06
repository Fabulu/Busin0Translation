import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def w32(m,va): return struct.unpack('<I',m[va:va+4])[0]
def h16(m,va): return struct.unpack('<H',m[va:va+2])[0]
def by(m,va): return m[va]
CTX=0x01137a00
W=load('C:/programmieren/wizardrytranslation/ramdumps/tavern104.p2s')
F=load('C:/programmieren/wizardrytranslation/ramdumps/fuckinghellman.p2s')
fields=[
 (0x000,'VM_PC (lw)','w'),
 (0x004,'+4','w'),
 (0x008,'+8','w'),
 (0x29C,'668 wait-cnt','h'),
 (0x2A2,'674 sm674 state','h'),
 (0x2A4,'676 sm676 state','h'),
 (0x296,'662','h'),
 (0x0D0,'208 flags','w'),
]
print(f'CTX=0x{CTX:08x}')
print(f'{"field":24}{"WORKING":>12}{"FROZEN":>12}  DIFF')
for off,nm,sz in fields:
    va=CTX+off
    if sz=='w': wv=w32(W,va); fv=w32(F,va); fmt='0x{:08x}'
    elif sz=='h': wv=h16(W,va); fv=h16(F,va); fmt='0x{:04x}'
    else: wv=by(W,va); fv=by(F,va); fmt='0x{:02x}'
    d='  <<<<DIFF' if wv!=fv else ''
    print(f'{nm:24}{fmt.format(wv):>12}{fmt.format(fv):>12}{d}')
# Dump VM PC target bytes (the opcode the VM is about to/just executed)
for lbl,m in [('WORKING',W),('FROZEN',F)]:
    pc=w32(m,CTX+0)
    print(f'\n{lbl} VM_PC=0x{pc:08x}')
    if 0x80000<pc<0x2000000:
        print('  bytes@PC:', m[pc-4:pc+12].hex())
