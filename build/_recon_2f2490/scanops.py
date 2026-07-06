import struct,sys,json
ee=open(sys.argv[1],'rb').read()
d=json.load(open(r'C:\programmieren\wizardrytranslation\build\recon_v85\exe-interpreter\opcode_table_v85.json'))
ops=d['opcodes']
def oplen(op):
    k=f'0x{op:02X}'
    return ops[k]['bytes'] if k in ops else 2
base=0x011C3D20
end=base+0x1000
i=base
found12=[];found1A=[]
while i < end:
    op=(ee[i]<<8)|ee[i+1]
    ln=oplen(op)
    if op>0xC0 or ln==0: break
    if op==0x12:
        off=struct.unpack('>I',ee[i+2:i+6])[0]
        found12.append((i-base,off))
    if op==0x1A:
        found1A.append(i-base)
    i+=ln
print("opcode 0x12 (CALL) sites:", [(hex(a),hex(b)) for a,b in found12])
print("opcode 0x1A (RETURN) sites:", [hex(a) for a in found1A])
