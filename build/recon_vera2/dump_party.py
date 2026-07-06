import sys
sys.stdout.reconfigure(encoding='utf-8')

EE = "../recon_tri/extract/veraisjapanese__ee.bin"
with open(EE,'rb') as f:
    ram = f.read()

def read_name(base):
    # name field at base+2, u16 LE glyph indices terminated by 0xFFFF
    out=[]
    p=base+2
    while True:
        v = ram[p] | (ram[p+1]<<8)
        if v==0xFFFF: break
        out.append(v)
        p+=2
        if len(out)>32: break
    return out

print("=== ACTIVE PARTY @0x55DD20 stride 0x1F0 ===")
base=0x55DD20
for i in range(6):
    s=base+i*0x1F0
    print(f"slot{i} @0x{s+2:X} = {read_name(s)}")

print()
print("=== RECRUIT POOL ~0x560000 stride 0x1F0 ===")
# scan a range around 0x560000 for FFFF-terminated glyph runs
base=0x560000
for i in range(16):
    s=base+i*0x1F0
    print(f"pool{i} @0x{s+2:X} = {read_name(s)}")
