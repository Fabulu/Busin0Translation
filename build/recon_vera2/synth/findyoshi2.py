import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
gojuon="あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
# よ index, し index, ほ index, く index
for ch in "よしほく":
    print(ch, gojuon.index(ch), "-> nv", 193+gojuon.index(ch))
vals=[193+gojuon.index(c) for c in "よしほく"]
print("よしほく name-values (base193):",vals)
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
pat=b''.join(struct.pack('<H',v) for v in vals)
i=0;hits=[]
while True:
    j=ee.find(pat,i)
    if j<0:break
    hits.append(j);i=j+1
    if len(hits)>30:break
print("よしほく occurrences:",[hex(h) for h in hits])
