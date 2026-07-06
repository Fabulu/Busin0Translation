import sys
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()

def hexd(off,n):
    out=[]
    for i in range(0,n,16):
        out.append(f"  0x{off+i:X}: "+' '.join(f'{b:02x}' for b in ram[off+i:off+i+16]))
    return '\n'.join(out)

def read_name(base):
    out=[];p=base
    while True:
        v=ram[p]|(ram[p+1]<<8)
        if v==0xFFFF:break
        out.append(v);p+=2
        if len(out)>40:break
    return out

# pool1 = Vera romanized at 0x5601F2 (name at +2, record 0x5601F0)
print("=== Pool1 (Vera ENGLISH) record @0x5601F0 ===")
print(hexd(0x5601F0,0x40))
print(" name:", read_name(0x5601F2))

# active slot1 Vera KATAKANA at 0x55DF10
print("\n=== Active slot1 (Vera KATA) record @0x55DF10 ===")
print(hexd(0x55DF10,0x40))
print(" name:", read_name(0x55DF12))

# Compare full 0x1F0 records to see what differs besides name
a=ram[0x55DF10:0x55DF10+0x1F0]
b=ram[0x5601F0:0x5601F0+0x1F0]
diffs=[i for i in range(0x1F0) if a[i]!=b[i]]
print(f"\nActive-slot1 vs Pool1 record: {len(diffs)} diffs, offsets: {[hex(x) for x in diffs[:30]]}")
