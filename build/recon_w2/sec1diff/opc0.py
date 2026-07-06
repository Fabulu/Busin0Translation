import json,sys
sys.stdout.reconfigure(encoding='utf-8')
t=json.load(open('build/recon_v85/exe-interpreter/opcode_table_v85.json',encoding='utf-8'))
ops=t['opcodes']
for k in ['0x0','0x00','0x04','0x06','0x07','0x08','0x0b','0x11','0x12','0x14','0x1a','0x43','0x45']:
    # normalize
    for kk in [k, '0x%02x'%int(k,16), hex(int(k,16))]:
        if kk in ops:
            print(kk, ops[kk]); break
