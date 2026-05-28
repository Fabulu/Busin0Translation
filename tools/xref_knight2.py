import struct,os
fp=os.path.join(r'C:\Programmieren\wizardrytranslation\extracted\packdata_resources','0046_type03.bin')
with open(fp,'rb') as f: d=f.read()
if len(d)%2: d=d[:-1]
vs=list(struct.unpack(f'>{len(d)//2}H',d))
s=chr(32)
for pos in [4193,1245]:
    nm=vs[pos+1:pos+4]
    t=[];j=pos+5
    while j<len(vs) and vs[j]!=0xFF01 and vs[j]!=0xFFFF:
        t.append(vs[j]);j+=1
    gl=[v for v in t if 0<v<=0x035A]
    fc=t.count(0xFFFE)
    h=[f'{v:04X}' for v in t]
    print(f'@{pos} nm={[hex(v) for v in nm]} {len(gl)}gl {fc}br')
    print(s+s.join(h))
    print()
