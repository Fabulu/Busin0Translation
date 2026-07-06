import struct,sys,json
ee=open(sys.argv[1],'rb').read()
d=json.load(open(r'C:\programmieren\wizardrytranslation\build\recon_v85\exe-interpreter\opcode_table_v85.json'))
ops=d['opcodes']
def oplen(op):
    k=f'0x{op:02X}'
    if k in ops: return ops[k]['bytes']
    return 2
base=0x011C3D20
end=base+0x600
i=base
while i < end:
    op=(ee[i]<<8)|ee[i+1]
    ln=oplen(op)
    body=ee[i:i+ln]
    hexs=' '.join(f'{x:02X}' for x in body)
    note=''
    if op==0x1A: note='  <<<<< OPCODE 0x1A (REBUILD handler 0x2F4450)'
    if op==0x06: note='  COND-JUMP'
    print(f"{i-base:04X}: op=0x{op:02X} len={ln}  [{hexs}]{note}")
    if op > 0xC0 or ln==0:
        print("  ! out of range, stop")
        break
    i+=ln
