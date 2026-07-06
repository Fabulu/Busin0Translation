import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8')
base=0x55DD20; stride=0x1F0
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def dec(v):
    # ascii name_val: 33..58 = A..Z if v in 33..90 range? player BABA had 33,34
    if 32<=v<=126-0: 
        # try ascii via (v - 32 + 0x20)?? slot0 had 34,33,34,33 = ABAB? need char
        pass
    if 193<=v<=193+44: return KATA[v-193]
    if v in KATA_EXTRA: return KATA_EXTRA[v]
    if 33<=v<=58: return chr(v-33+ord('A'))  # A=33
    if 65<=v<=90: return chr(v-65+ord('a'))
    return f'<{v}>'
for f in sorted(glob.glob("C:/programmieren/wizardrytranslation/build/recon_tri/extract/*__ee.bin")):
    ee=open(f,'rb').read()
    print("==",os.path.basename(f))
    for s in range(6):
        o=base+s*stride+2; vals=[]; p=o
        while True:
            v=ee[p]|(ee[p+1]<<8)
            if v==0xFFFF: break
            vals.append(v); p+=2
            if len(vals)>16: break
        print(f"  slot{s} {vals} = {''.join(dec(v) for v in vals)}")
