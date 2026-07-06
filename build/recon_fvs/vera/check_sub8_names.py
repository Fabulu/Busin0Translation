import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
prist=open('extracted/packdata_raw/2654_type44.raw','rb').read()
KATA_BASE=193
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',232:'ラ',258:'ボ',257:'ベ',269:'ャ',265:'ョ',267:'ァ',268:'ゥ',239:'ヲ',241:'ガ',243:'グ',244:'ゲ',259:'パ',260:'ピ',261:'ク',262:'シ',263:'ハ',264:'リ',271:'ォ',256:'ブ'}
def k(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    if 95<=nv<=189: return chr((nv-95)+0x20)
    return EXTRA.get(nv,f'<{nv}>')
def hdr(r): return [dict(zip(('sub','size','off','z'), struct.unpack_from('<4I', r, i*16))) for i in range(44)]
H=hdr(prist)
def name_prefix_of(seg):
    # name is the run before 0x001d separator
    words=[struct.unpack_from('>H',seg,p)[0] for p in range(0,len(seg)-1,2)]
    s=[]
    for w in words:
        if w==0x001d or w==0xFFFE or w==0xFFFF: break
        s.append(k(w))
    return ''.join(s)
for subn in (8,):
    h=next(x for x in H if x['sub']==subn)
    off,size=h['off'],h['size']
    cnt=struct.unpack_from('>H',raw if False else prist,off)[0]
    offs=[struct.unpack_from('>H',prist,off+4+i*4)[0] for i in range(cnt)]
    print(f'sub{subn} name prefixes ({cnt} entries):')
    for i in range(cnt):
        st=off+offs[i]; en=off+(offs[i+1] if i+1<cnt else size)
        print(f'  {i:2d}: {name_prefix_of(prist[st:en])}')
