import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
KATA_BASE=193
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ',232:'ラ',258:'ボ',257:'ベ',269:'ャ',265:'ョ',267:'ァ',268:'ゥ',239:'ヲ',241:'ガ',243:'グ',244:'ゲ',259:'パ',260:'ピ',261:'ク',262:'シ',263:'ハ',264:'リ',271:'ォ',256:'ブ',255:'ビ',266:'ヌ',240:'ザ',242:'ギ'}
def k(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    if 95<=nv<=189: return chr((nv-95)+0x20)
    return EXTRA.get(nv,f'<{nv}>')

d=open('extracted/packdata_raw/1892_type20.raw','rb').read()
print(f'R1892 size={len(d)} ({len(d)//2048} sectors)')
# Decode as LE u16 stream from start (since LE Basco at 0x272 and Vera LE at 0xbf2)
print('\n--- LE u16 dump 0x260..0xc20 with kana ---')
o=0x260
prev_term=True
buf=[]
def flush(start,buf):
    if buf:
        s=''.join(k(w) for w in buf)
        print(f'  0x{start:04x}: {s}   [{" ".join(f"{w:04x}" for w in buf)}]')
start=o
while o < 0xc40:
    w=struct.unpack_from('<H',d,o)[0]
    if w in (0xFFFF,0xFFFE,0x0000):
        flush(start,buf); buf=[]
        o+=2; start=o; continue
    buf.append(w); o+=2
flush(start,buf)

# header: how many entries? check first 16 bytes (type20 = container?)
print('\n--- first 32 bytes (LE u32) ---')
for i in range(8):
    print(f'  +{i*4:02x}: {struct.unpack_from("<I",d,i*4)[0]:08x}')
