import struct, json
ee=open("runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/dungeon_menus/untranslatedmessidalogue/eeMemory.bin","rb").read()
print("ee size", len(ee))
# search for [297,280,286] big-endian u16 = 01 29 01 18 01 1E
pat=struct.pack(">HHH",297,280,286)
i=ee.find(pat); cnt=0; offs=[]
while i!=-1 and cnt<20:
    offs.append(i); cnt+=1; i=ee.find(pat,i+2)
print("BE [297,280,286] hits:",cnt, [hex(o) for o in offs[:10]])
# also little-endian
patle=struct.pack("<HHH",297,280,286)
j=ee.find(patle); print("LE first hit:", hex(j) if j!=-1 else None)
# search 4-glyph with 長 candidates appended
for cho in (383,660,1051,1190,290):  # try several
    p=struct.pack(">HHHH",297,280,286,cho)
    k=ee.find(p)
    if k!=-1: print("4-glyph BE +",cho,"@",hex(k))
