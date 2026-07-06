import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
ee=open(f'{BASE}/build/recon_portrait4/extract/request__ee.bin','rb').read()
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv(v):
    if 193<=v<=193+44: return KATA[v-193]
    if 95<=v<=189: return chr((v-95)+0x20)
    return KATA_EXTRA.get(v,'?%d?'%v)
# Vera is the active SECOND party member -> its record is in active party array.
# The Vera active copy: there are only 2 Vera copies (0x5601f2 roster, 0xdc1af2). 
# The party bar shows leader THEN Vera. So leader record precedes Vera's ACTIVE copy.
# But 0xdc1af2 region is the savegame char-db (stride 304). Active party is a separate small array.
# Let's find where the game points to active party-member records. Search for a name 'A A' rendered.
# 'A'=name_val 128 (0x80). 'A A' could be 3 chars: 128, <space>, 128. space glyph=0x0000 per CLAUDE.
# But maybe leader name stored as TWO single 'A' (first/last name) fields.
# Search all 0x0080 0x0000 0x0080 anywhere:
import struct as st
pat=st.pack('<3H',128,0,128)
s=0;hits=[]
while True:
    i=ee.find(pat,s)
    if i<0:break
    hits.append(i);s=i+1
print("128,0,128 hits:",['0x%x'%h for h in hits[:30]])
# Maybe leader name is 0x80 FFFF 0x80 FFFF (two 1-char name fields 'A')
pat2=st.pack('<4H',128,0xFFFF,128,0xFFFF)
s=0;hits2=[]
while True:
    i=ee.find(pat2,s)
    if i<0:break
    hits2.append(i);s=i+1
print("128,FFFF,128,FFFF hits:",['0x%x'%h for h in hits2[:30]])
# single 'A' name field followed by FFFF
pat3=st.pack('<2H',128,0xFFFF)
s=0;hits3=[]
while True:
    i=ee.find(pat3,s)
    if i<0:break
    hits3.append(i);s=i+1
print("128,FFFF count:",len(hits3),'first:',['0x%x'%h for h in hits3[:20]])
