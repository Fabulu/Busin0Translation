#!/usr/bin/env python3
"""RECON 2 verification: prove the lifecycle facts against EXE disasm + both RAM dumps.
Run: python build/recon_lifecycle/VERIFY.py"""
import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def v2f(va): return va-0x100000+0x80
def word(va): return struct.unpack('<I',data[v2f(va):v2f(va)+4])[0]
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
W=load('C:/programmieren/wizardrytranslation/ramdumps/tavern104.p2s')   # working (pre-Requests)
F=load('C:/programmieren/wizardrytranslation/ramdumps/fuckinghellman.p2s') # frozen (post)
def w32(m,va): return struct.unpack('<I',m[va:va+4])[0]
GP=0x504FF0
ok=True
def check(name,cond,detail=''):
    global ok
    ok = ok and cond
    print(f'[{"PASS" if cond else "FAIL"}] {name} {detail}')

print('=== FACT 1: flag 0x4FE690 (gp-0x6960) has NO live reader ===')
# getter 0x2F16B0 reads it; verify getter has 0 jal callers and is not stored as data ptr
jal690=[]
for off in range(0,len(data)-3,4):
    w=struct.unpack('<I',data[off:off+4])[0]
    if (w>>26)==3:
        tgt=(((off-0x80+0x100000)+4)&0xf0000000)|((w&0x3ffffff)<<2)
        if tgt==0x2F16B0: jal690.append(off-0x80+0x100000)
ptr690=[off for off in range(0,len(data)-3,4) if struct.unpack('<I',data[off:off+4])[0]==0x2F16B0]
check('getter 0x2F16B0 caller count == 0', len(jal690)==0, f'callers={[hex(x) for x in jal690]}')
check('getter 0x2F16B0 not stored as data ptr', len(ptr690)==0, f'ptrs={len(ptr690)}')

print('\n=== FACT 2: flag values (diff confirms LEAD1 flipped 1->0 but reader is dead) ===')
for va,nm in [(0x4FE690,'FLAG690'),(0x4FE6B8,'FLAG6B8'),(0x4FE724,'FLAG724')]:
    print(f'   {nm}: working={W[va]} frozen={F[va]}')
check('FLAG690 working=1 frozen=0', W[0x4FE690]==1 and F[0x4FE690]==0)

print('\n=== FACT 3: window-state flag 0x4FE918 identical -> mgr WOULD respawn task 0x3A2440 in both ===')
check('0x4FE918 working==frozen', W[0x4FE918]==F[0x4FE918], f'=0x{W[0x4FE918]:02x}')
# spawn gate at 0x3A26E8: spawn iff (val & 1)==0 and (val & 4)==0
g=lambda v:(v&1)==0 and (v&4)==0
check('spawn-gate(0x4FE918) true in BOTH (task 3A2440 is transient)', g(W[0x4FE918]) and g(F[0x4FE918]))

print('\n=== FACT 4: manager task 0x3A25F0 present (would respawn 3A2440) in both lists ===')
def listfns(m):
    head=w32(m,0x578CC4); cur=head; seen=set(); fns=[]
    while cur and cur not in seen and 0x500000<cur<0x600000 and len(fns)<40:
        seen.add(cur); fns.append(w32(m,cur+8)); cur=w32(m,cur+0)
    return fns
wf=listfns(W); ff=listfns(F)
check('mgr 0x3A25F0 in WORKING list', 0x3A25F0 in wf)
check('mgr 0x3A25F0 in FROZEN list', 0x3A25F0 in ff)
check('task 0x3A2440 only in WORKING (per-frame phase artifact)', (0x3A2440 in wf) and (0x3A2440 not in ff))

print('\n=== FACT 5: hub handler 0x2F2490 installed as curScreen fn in BOTH ===')
def curfn(m): return w32(m, w32(m,GP-25136)+8)
check('curScreen fn == 0x2F2490 in WORKING', curfn(W)==0x2F2490)
check('curScreen fn == 0x2F2490 in FROZEN', curfn(F)==0x2F2490)

print('\n=== FACT 6: all hub-task input gates identical (would NOT skip input if task ran) ===')
gates={'0x4FE684':GP-26948,'0x4FE664':GP-26980,'0x4FE53C':GP-29492,'0x4FE678(input)':GP-26956}
allsame=True
for nm,va in gates.items():
    wv=W[va] if 'input' not in nm else w32(W,va)
    fv=F[va] if 'input' not in nm else w32(F,va)
    if wv!=fv: allsame=False
    print(f'   {nm}: working={wv} frozen={fv}')
check('all hub input gates identical', allsame)

print('\n=== FACT 7: VM context (0x01137a00) byte-identical incl VM_PC ===')
CTX=0x01137a00
check('VM_PC identical', w32(W,CTX)==w32(F,CTX), f'=0x{w32(W,CTX):08x}')
check('VM ctx[0:0x300] byte-identical', W[CTX:CTX+0x300]==F[CTX:CTX+0x300])

print('\n================ CONCLUSION ================')
print('All proposed static leads are EQUIVALENT or dead in both dumps.')
print('No static RAM flag/task/handler explains a GLOBAL input freeze.')
print('OVERALL:', 'ALL CHECKS PASS' if ok else 'SOME CHECKS FAILED')
