import sys,os
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()
pristine=open("../../extracted/packdata_raw/1892_type20.raw",'rb').read()

# Is build/packdata_resources/1892_type20.raw present (patched)?
patched_fp="../../build/packdata_resources/1892_type20.raw"
patched=open(patched_fp,'rb').read() if os.path.exists(patched_fp) else None
print("patched R1892 exists:", patched is not None)

def read_name(data,base):
    out=[];p=base
    while True:
        v=data[p]|(data[p+1]<<8)
        if v==0xFFFF:break
        out.append(v);p+=2
        if len(out)>40:break
    return out

if patched:
    print("PRISTINE Vera @0x142:", read_name(pristine,0x142))
    print("PATCHED  Vera @0x142:", read_name(patched,0x142))

# 0xDC0F00 buffer Vera = katakana = matches PRISTINE
buf=ram[0xDC0F00:0xDC0F00+8192]
dp=sum(1 for i in range(8192) if buf[i]!=pristine[i])
print(f"\n0xDC0F00 buffer vs PRISTINE R1892: {dp} diffs")
if patched:
    dpp=sum(1 for i in range(8192) if buf[i]!=patched[i])
    print(f"0xDC0F00 buffer vs PATCHED  R1892: {dpp} diffs")

# Now check: which ISO was this dump from? Look at pool which is English.
# The pool English names mean SOMETHING was patched. Compare pool name encoding
# to patched R1892 name-values.
print("\nPool1 Vera name (RAM 0x5601F2):", read_name(ram,0x5601F2))
if patched:
    print("Patched R1892 Vera name        :", read_name(patched,0x142))
