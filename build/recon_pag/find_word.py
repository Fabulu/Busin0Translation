import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
D=open('extracted/SLPM_653.78','rb').read()
def f2v(off): return off-0x80+0x100000
targets=[int(x,16) for x in sys.argv[1:]]
for tgt in targets:
    tb=struct.pack('<I',tgt)
    print('=== word %08x occurrences ==='%tgt)
    idx=0
    cnt=0
    while True:
        i=D.find(tb, idx)
        if i<0: break
        print('  at file %08x (vaddr %08x)'%(i, f2v(i)))
        idx=i+4
        cnt+=1
        if cnt>40: print('  ...more'); break
