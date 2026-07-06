import sys,os
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()

def read_name(data,base):
    out=[];p=base
    while True:
        v=data[p]|(data[p+1]<<8)
        if v==0xFFFF:break
        out.append(v);p+=2
        if len(out)>40:break
    return out

# Copy A: 0xDC0F00 buffer (active party source). Vera rec at 0xDC1042
print("=== Copy A @0xDC0F00 (active-party source) ===")
print(" Vera name @0xDC1042:", read_name(ram,0xDC1042))

# Copy B: search for romanized roster near 0x560000. The pool@0x560000 used stride 0x1F0
# but is there ALSO a 0x130-stride R1892 copy that's romanized?
# Search whole RAM for R1892 directory signature to find ALL load copies
sig = bytes.fromhex("0000000030010000400100000000000001000000300100007002000000000000")
locs=[];start=0
while True:
    i=ram.find(sig,start)
    if i<0:break
    locs.append(i);start=i+1
print(f"\nR1892 directory signature found at {len(locs)} RAM locations: {[hex(x) for x in locs]}")
for L in locs:
    # Vera record at L + 0x140 + 2
    print(f"  @0x{L:X}: Vera name @0x{L+0x142:X} = {read_name(ram,L+0x142)}")
