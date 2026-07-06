import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
base=0x55DD20; stride=0x1F0
for s in [0,1]:
    rs=base+s*stride
    print(f"=== slot{s} @0x{rs:X} ===")
    chunk=ee[rs:rs+0x60]
    for i in range(0,0x60,16):
        row=chunk[i:i+16]
        hexs=' '.join(f'{b:02x}' for b in row)
        u16s=' '.join(f'{struct.unpack_from("<H",row,j)[0]:5d}' for j in range(0,16,2))
        print(f"  +{i:03X}: {hexs}")
        print(f"        u16: {u16s}")
