import struct
d=open('C:/Programmieren/wizardrytranslation/ee_memory_fight1.bin','rb').read()
off=0x4C9CE0
ctx=d[off:off+800]
vals=list(struct.unpack('<'+str(len(ctx)//2)+'H',ctx))
for row in range(12):
    rowvals = []
    for col in range(8):
        idx = (row*8+col)*2
        if idx+1 < len(vals):
            v = vals[idx]
            if v == 65535:
                rowvals.append('---')
            elif v == 0:
                rowvals.append('...')
            else:
                rowvals.append(str(v))
        else:
            rowvals.append('?')
    print('Row ' + str(row) + ': ' + str(rowvals))
