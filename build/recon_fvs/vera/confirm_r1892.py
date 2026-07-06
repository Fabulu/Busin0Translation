import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
KATA_BASE=193
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',232:'ラ',258:'ボ',257:'ベ',269:'ャ',265:'ョ',267:'ァ',268:'ゥ',239:'ヲ',241:'ガ',243:'グ',244:'ゲ',259:'パ',260:'ピ',261:'ク',262:'シ',263:'ハ',264:'リ',271:'ォ',256:'ブ',255:'ビ',266:'ヌ',240:'ザ',242:'ギ'}
def k(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    if 95<=nv<=189: return chr((nv-95)+0x20)
    return EXTRA.get(nv,f'<{nv}>')
d=open('extracted/packdata_raw/1892_type20.raw','rb').read()

# records stride 0x1f0, first at 0x270. Vera LE at 0xbf2 per scan.
# Find record base for Vera: 0x270 + n*0x1f0
print('R1892 record map (base: id: name LE):')
base=0x270
for n in range(20):
    o=base+n*0x1f0
    if o+0x20>len(d): break
    rid=struct.unpack_from('<H',d,o)[0]
    # name follows id: name at o+2
    s=[]
    for j in range(8):
        w=struct.unpack_from('<H',d,o+2+j*2)[0]
        if w in (0,0xffff,0xfffe): break
        s.append(k(w))
    nm=''.join(s)
    mark=' <== VERA' if 'ヴェーラ' in nm else ''
    print(f'  0x{o:04x}: id={rid:3d}  {nm}{mark}')

# Confirm Vera record
print('\nVera record (0xbf0 area): name offset check')
# 0xbf2 was LE Vera. record base = 0xbf2-2 = 0xbf0
o=0xbf0
print(f'  id@0x{o:04x} = {struct.unpack_from("<H",d,o)[0]}')
for j in range(6):
    print(f'    name+{j*2}: {struct.unpack_from("<H",d,o+2+j*2)[0]:04x} = {k(struct.unpack_from("<H",d,o+2+j*2)[0])}')

# name field offset within record = +2
# In RAM, Vera name at 0x5601f2, so RAM record base = 0x5601f0. id at 0x5601f0?
ee=open('build/recon_portrait4/extract/request__ee.bin','rb').read()
print('\nRAM Vera record base 0x5601f0 id =', struct.unpack_from('<H',ee,0x5601f0)[0], '(c001 = LE 0x01c0 = 448)')
# Hmm RAM id field differs. Check if R1892 record is copied to RAM with id replaced.
# Compare R1892 Vera record bytes vs RAM record bytes
r1892_vera = d[0xbf0:0xbf0+0x1f0]
ram_vera = ee[0x5601f0:0x5601f0+0x1f0]
# count matching bytes
match=sum(1 for a,b in zip(r1892_vera,ram_vera) if a==b)
print(f'R1892 Vera record vs RAM record: {match}/{0x1f0} bytes match')
# show first 0x30 of each
print('R1892:', ' '.join(f'{x:02x}' for x in r1892_vera[:0x30]))
print('RAM  :', ' '.join(f'{x:02x}' for x in ram_vera[:0x30]))
