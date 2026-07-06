import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
b=open('extracted/packdata_raw/1892_type20.raw','rb').read()
print('R1892 len',len(b))
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EX={93:'ー',238:'ン',270:'ェ',273:'ヴ',252:'デ',265:'ー',239:'サ',257:'ハ',241:'チ',243:'ト',267:'ィ'}
def k(nv):
    if 193<=nv<=237: return KATA[nv-193]
    return EX.get(nv,f'<{nv}>')
def name_at(p):
    s=''
    for q in range(p,p+40,2):
        w=struct.unpack_from('<H',b,q)[0]
        if w in (0xFFFF,0): break
        if 95<=w<=189: s+=chr(w-95+0x20)
        else: s+=k(w)
    return s
# vera at 3058=0xBF2. find table structure
print('vera at 0x%X'%3058)
# scan for all LE name runs
print('=== all LE name runs in R1892 ===')
p=0
prev=None
while p<len(b)-8:
    w=struct.unpack_from('<H',b,p)[0]
    if (128<=w<=153) or (193<=w<=273):
        nm=name_at(p)
        if len(nm)>=2 and '<' not in nm:
            if prev is not None:
                print('  0x%X (+0x%X) %r'%(p,p-prev,nm))
            else:
                print('  0x%X %r'%(p,nm))
            prev=p
            p+=2; continue
    p+=2
