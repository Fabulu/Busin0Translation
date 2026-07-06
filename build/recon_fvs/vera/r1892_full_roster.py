import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
KATA_BASE=193
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',232:'ラ',258:'ボ',257:'ベ',269:'ャ',265:'ョ',267:'ァ',268:'ゥ',239:'ヲ',241:'ガ',243:'グ',244:'ゲ',259:'パ',260:'ピ',261:'ク',262:'シ',263:'ハ',264:'リ',271:'ォ',256:'ブ',255:'ビ',266:'ヌ',240:'ザ',242:'ギ'}
def k(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    if 95<=nv<=189: return chr((nv-95)+0x20)
    return EXTRA.get(nv,f'<{nv}>')
d=open('extracted/packdata_raw/1892_type20.raw','rb').read()
# scan full file for ALL records: stride 0x1f0 from 0x270? But file is only 8192 bytes = 16 records.
# Records confirmed at 0x270,0x3a0,0x4d0,0x600,0x730,0x860,... that's stride 0x130! NOT 0x1f0.
# 0x3a0-0x270=0x130=304. Let me recompute.
print('record starts (by scanning for id+kana name):')
bases=[0x270,0x3a0,0x4d0,0x600,0x730,0x860]
for i in range(1,len(bases)):
    print(f'  stride {bases[i]-bases[i-1]:#x}')
# So file stride = 0x130. RAM stride = 0x1f0. Different! RAM record is expanded.
# List all records in file:
print('\nR1892 file records (stride 0x130 from 0x270):')
o=0x270; i=0
while o+0x10<=len(d):
    rid=struct.unpack_from('<H',d,o)[0]
    s=[]
    for j in range(8):
        w=struct.unpack_from('<H',d,o+2+j*2)[0]
        if w in (0,0xffff,0xfffe): break
        s.append(k(w))
    nm=''.join(s)
    if nm or rid:
        print(f'  0x{o:04x}: id={rid:5d}  name_LE={nm}')
    o+=0x130; i+=1
