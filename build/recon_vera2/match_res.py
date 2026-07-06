import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()

dir_start=0xDC0F00
# entry16 rel=0x1440, Vera name record at 0xDC1042 (record header at 0xDC1040, name+2)
# so buffer_base + 0x1440 = 0xDC1040? -> base = 0xDC1040-0x1440 = 0xDBFC00
base = 0xDC1040 - 0x1440
print(f"buffer base = 0x{base:X}, dir_start=0x{dir_start:X}, dir offset in buf = 0x{dir_start-base:X}")
# count entries
n=0
while True:
    off=dir_start+n*16
    size=int.from_bytes(ram[off+4:off+8],'little')
    if size!=0x130: break
    n+=1
print(f"entry count = {n}")
# total buffer extent: last record end
last_rel=int.from_bytes(ram[dir_start+(n-1)*16+8:dir_start+(n-1)*16+12],'little')
buf_end=base+last_rel+0x130
print(f"buffer 0x{base:X} .. 0x{buf_end:X} ({buf_end-base} bytes)")

# Take a signature chunk from the directory and search packdata_raw
sig = ram[dir_start:dir_start+256]
print("\nsig hex (dir):", sig[:48].hex())

# Search extracted/packdata_raw and packdata_resources
roots=["../../extracted/packdata_raw","../../extracted/packdata_resources"]
hits=[]
for root in roots:
    if not os.path.isdir(root): 
        print("missing",root); continue
    files=glob.glob(os.path.join(root,"*"))
    for fp in files:
        if os.path.isdir(fp): continue
        try:
            data=open(fp,'rb').read()
        except: continue
        if sig in data:
            hits.append((fp,data.find(sig)))
print("\nDirectory-sig hits in packdata:")
for h in hits: print("  ",h[0],hex(h[1]))
print(f"\n(searched roots, files found)")
for root in roots:
    print(" ",root, len(glob.glob(os.path.join(root,"*"))) if os.path.isdir(root) else "N/A")
