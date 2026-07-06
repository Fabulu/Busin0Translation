import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
b=open('extracted/packdata_raw/1892_type20.raw','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EX={93:'ー',238:'ン',270:'ェ',273:'ヴ',252:'デ',265:'ー',239:'サ',257:'ハ',241:'チ',243:'ト',267:'ィ'}
def k(nv):
    if 193<=nv<=237: return KATA[nv-193]
    return EX.get(nv,f'<{nv}>')
def name_at(buf,p):
    s=''
    for q in range(p,p+40,2):
        w=struct.unpack_from('<H',buf,q)[0]
        if w in (0xFFFF,0): break
        if 95<=w<=189: s+=chr(w-95+0x20)
        else: s+=k(w)
    return s
# header of R1892 - type20 likely has a header; vera at 0xBF2, stride 0x130
# Vera record start: name at +0, find record base. records: 0xBF2,0xD22,0xE52,0xF82 -> stride 0x130
# So record base = name offset (name at struct+0)
print('=== R1892 records stride 0x130 from first ===')
# first real record: 0x142? but 0x142-0x130 etc. Let's anchor on Vera and walk back
base=0xBF2
# walk back to find table start
recs=[]
p=base
while p>=0:
    nm=name_at(b,p)
    recs.append((p,nm)); p-=0x130
recs=recs[::-1]
p=base+0x130
while p<len(b):
    recs.append((p,name_at(b,p))); p+=0x130
for off,nm in recs:
    # dump header bytes of record
    hd=b[off-2:off].hex() if off>=2 else ''
    print('  0x%04X  pre=%s  name=%r'%(off,hd,nm))
print()
print('=== R1892 header (first 0x142 bytes) as u16 LE ===')
for p in range(0,0x20,2):
    print('  0x%X: %d'%(p,struct.unpack_from('<H',b,p)[0]))
