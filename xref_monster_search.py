import struct
d=open('C:/Programmieren/wizardrytranslation/ee_memory_fight1.bin','rb').read()
base = 0xE14700
n = 400
vals = [struct.unpack_from('>H', d, base+i*2)[0] for i in range(n)]
for i in range(0, n, 20):
    chunk = vals[i:i+20]
    readable = []
    for v in chunk:
        if v == 0xFFFF:
            readable.append('FFFF')
        elif v == 0xFFFE:
            readable.append('FFFE')
        elif v <= 858:
            readable.append(str(v))
        else:
            readable.append(hex(v))
    print(f'{hex(base+i*2)}: {readable}')
