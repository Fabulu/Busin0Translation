import sys,os,glob
sys.stdout.reconfigure(encoding='utf-8')
def pat(ids): return b''.join((v&0xFFFF).to_bytes(2,'little') for v in ids)

vera_kata=pat([193,194,232,205])
roots=["../../extracted/packdata_raw","../../extracted/packdata_resources"]
print("Searching for Vera katakana [193,194,232,205] u16LE:")
for root in roots:
    for fp in glob.glob(os.path.join(root,"*")):
        if os.path.isdir(fp):continue
        try:data=open(fp,'rb').read()
        except:continue
        i=data.find(vera_kata)
        if i>=0:
            print(f"  {os.path.basename(fp)} @0x{i:X}")

# Also check the romanized Vera in pool: [149,164,177,160] = "Vera" base63
vera_rom=pat([149,164,177,160])
print("\nSearching for Vera romanized [149,164,177,160] u16LE:")
for root in roots:
    for fp in glob.glob(os.path.join(root,"*")):
        if os.path.isdir(fp):continue
        try:data=open(fp,'rb').read()
        except:continue
        i=data.find(vera_rom)
        if i>=0:
            print(f"  {os.path.basename(fp)} @0x{i:X}")
