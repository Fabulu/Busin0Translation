import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
ee=open(f'{BASE}/build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv(v):
    if 193<=v<=193+44: return KATA[v-193]
    if 95<=v<=189: return chr((v-95)+0x20)
    return KATA_EXTRA.get(v,'')
def decode_name(off):
    vals=struct.unpack_from('<8H',ee,off)
    s=''
    for v in vals:
        if v==0xFFFF or v==0: break
        s+=nv(v) or '?%d?'%v
    return s,vals
# Vera record appears to start at 0x5601f2 (name at offset 0). 
# Party records likely a fixed-stride array. Vera is 2nd char. Find leader by scanning backward.
# stride guess: try to find a preceding name. Search region 0x55f000..0x561000 for name-like u16 runs
print('Vera name @0x5601f2:', decode_name(0x5601f2)[0])
# A leader 'A A' : 'A'=name_val 0x95+? ascii. 'A' ascii gid? char A.
# If leader shows ascii 'A A', that's romaji already. name_val for 'A': from glyph table.
import json
gt=json.load(open(f'{BASE}/data/english_glyph_table.json',encoding='utf-8'))
print("glyph 'A'=",gt.get('A'),"-> name_val",(gt.get('A',0)+95))
print("glyph ' '=",gt.get(' '),"space")
# 'A A' => name_vals for A, space, A
aval=gt['A']+95
# search for A <space> A pattern in LE u16
import struct as st
sp_candidates=[0,gt.get(' ',0)+95 if ' ' in gt else 95]
for spv in set([0,95]+([gt[' ']+95] if ' ' in gt else [])):
    pat=st.pack('<HHH',aval,spv,aval)
    s=0; hits=[]
    while True:
        i=ee.find(pat,s)
        if i<0: break
        hits.append(i); s=i+1
        if len(hits)>30: break
    print(f"'A {spv} A' nv=({aval},{spv},{aval}) pat={pat.hex()}: {len(hits)} hits -> "+', '.join('0x%x'%h for h in hits[:15]))
