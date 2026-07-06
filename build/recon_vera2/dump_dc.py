import sys
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()

# The 0xDC1xxx copies. slot1 at 0xdc1042, slot2 at 0xdc1172 -> stride
locs=[0xdc1042,0xdc1172,0xdc12a2,0xdc13d2,0xdc1502]
for i in range(1,len(locs)):
    print(f"stride {i}: 0x{locs[i]-locs[i-1]:X}")
# stride looks ~0x130. name at +? offset within record. base of record?
# 0xdc1042 - what's around it
def hexdump(off,n=0x40):
    b=ram[off:off+n]
    out=[]
    for i in range(0,len(b),16):
        chunk=b[i:i+16]
        hx=' '.join(f'{x:02x}' for x in chunk)
        out.append(f"  0x{off+i:X}: {hx}")
    return '\n'.join(out)

print("\n=== Region before 0xDC1042 (find record start) ===")
print(hexdump(0xdc1000,0x80))
print("\n=== name field as u16 ===")
def read_name(base):
    out=[];p=base
    while True:
        v=ram[p]|(ram[p+1]<<8)
        if v==0xFFFF: break
        out.append(v); p+=2
        if len(out)>32: break
    return out
print("at 0xdc1042:", read_name(0xdc1042))
