import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EX={93:'ー',238:'ン',270:'ェ',273:'ヴ',252:'デ',265:'ー',239:'サ'}
def k(nv):
    if 193<=nv<=237: return KATA[nv-193]
    return EX.get(nv,f'<{nv}>')
def name_at(p):
    s=''
    for q in range(p,p+40,2):
        w=struct.unpack_from('<H',ee,q)[0]
        if w in (0xFFFF,0): break
        if 95<=w<=189: s+=chr(w-95+0x20)
        else: s+=k(w)
    return s
# dc1 region: Vera@0xDC1AF2, Konde@0xDC1D52, Iris@0xDC1E82. stride?
print('Konde-Vera=0x%X  Iris-Konde=0x%X'%(0xDC1D52-0xDC1AF2,0xDC1E82-0xDC1D52))
# stride ~0x130? walk
print('=== dc1 region walk ===')
base=0xDC1AF2
for i in range(-2,8):
    p=base+i*0x130
    print('  i%2d 0x%X %r'%(i,p,name_at(p)))
print('--- try active party slots: scan 0xDC1000..0xDC2800 for names ---')
p=0xDC1800
while p<0xDC2800:
    w=struct.unpack_from('<H',ee,p)[0]
    if (128<=w<=153) or (193<=w<=273):
        nm=name_at(p)
        if len(nm)>=2 and '<' not in nm:
            print('  0x%X %r'%(p,nm))
    p+=2
