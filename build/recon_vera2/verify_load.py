import sys
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()
r1892=open("../../extracted/packdata_raw/1892_type20.raw",'rb').read()

# Vera name record in RAM at 0xDC1042 (name+2 -> record header 0xDC1040)
# In file, Vera glyph run at 0x142 -> record header 0x140
# So RAM 0xDC1040 corresponds to file 0x140 => base = 0xDC1040-0x140 = 0xDC0F00
base = 0xDC1040-0x140
print(f"buffer base = 0x{base:X}")
buf=ram[base:base+len(r1892)]
diffs=[i for i in range(len(r1892)) if buf[i]!=r1892[i]]
print(f"R1892({len(r1892)}B) vs RAM@0x{base:X}: {len(diffs)} diffs")
if diffs[:10]: print("first diffs:",[hex(x) for x in diffs[:10]])

# Show the record layout: file directory
print("\nFile R1892 header (first 0x60):")
for i in range(0,0x60,16):
    print(" ",f"0x{i:X}:",' '.join(f'{b:02x}' for b in r1892[i:i+16]))

def read_name(data,base):
    out=[];p=base
    while True:
        v=data[p]|(data[p+1]<<8)
        if v==0xFFFF:break
        out.append(v);p+=2
        if len(out)>32:break
    return out
print("\nFile Vera record header @0x140:",' '.join(f'{b:02x}' for b in r1892[0x140:0x150]))
print("File Vera name @0x142:",read_name(r1892,0x142))
