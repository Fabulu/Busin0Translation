import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
KATA_BASE=193
KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA = {93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv_to_kana(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    return KATA_EXTRA.get(nv,f'<{nv}>')
def dec(words):
    s=[]
    for w in words:
        if w==0xFFFF: break
        if w==0xFFFE: continue
        if 95<=w<=189: s.append(chr((w-95)+0x20))
        else: s.append(nv_to_kana(w))
    return ''.join(s)

raw=open('build/recon_fvs/vera/r2654_from_v92iso.raw','rb').read()
# sub 8: off 0x8540 size 0x208a -- dump around 0x8a4c
print('=== sub8 raw around 0x8a4c (the katakana Vera) ===')
base=0x8540
# is sub8 a table-of-offsets format like sub7?
cnt=struct.unpack_from('>H',raw,base)[0]
print(f'sub8 first word (count?) = {cnt}')
# dump context
for o in range(0x8a30, 0x8a90, 2):
    w=struct.unpack_from('>H',raw,o)[0]
    print(f'  0x{o:06x}: {w:04x}  {nv_to_kana(w) if w>0x40 else ""}')

print('\n=== sub33 raw around 0x34ab8 ===')
for o in range(0x34aa0, 0x34b00, 2):
    w=struct.unpack_from('>H',raw,o)[0]
    print(f'  0x{o:06x}: {w:04x}  {nv_to_kana(w) if w>0x40 else ""}')
