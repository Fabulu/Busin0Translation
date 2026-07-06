import sys
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()
r1892=open("../../extracted/packdata_raw/1892_type20.raw",'rb').read()
print("R1892 file size:", len(r1892))

base=0xDBFC00
# buffer extent 6400 bytes
buf=ram[base:base+0x1500]
# Compare to R1892 file
minlen=min(len(buf),len(r1892))
diffs=[]
for i in range(minlen):
    if buf[i]!=r1892[i]:
        diffs.append(i)
print(f"compared {minlen} bytes, {len(diffs)} differences")
if diffs:
    print("first diff offsets:", [hex(x) for x in diffs[:20]])

# Vera record: file offset 0x1440 (record header), name at 0x1442
def read_name(data,base):
    out=[];p=base
    while True:
        v=data[p]|(data[p+1]<<8)
        if v==0xFFFF: break
        out.append(v);p+=2
        if len(out)>32:break
    return out
print("\nR1892 FILE record16 name @0x1442:", read_name(r1892,0x1442))
print("RAM buffer  record16 name @0x1442:", read_name(buf,0x1442))

# Show what 'romanized' would look like - check name_labels / r2654 json
