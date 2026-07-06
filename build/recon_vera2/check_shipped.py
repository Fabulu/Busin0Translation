import sys,glob,os
sys.stdout.reconfigure(encoding='utf-8')
def read_name(data,base):
    out=[];p=base
    while True:
        v=data[p]|(data[p+1]<<8)
        if v==0xFFFF:break
        out.append(v);p+=2
        if len(out)>40:break
    return out

# Find shipped R1892 in build output / packdata_resources
cands=glob.glob("../../extracted/packdata_resources/*1892*")+glob.glob("../../extracted/packdata_raw/*1892*")+glob.glob("../../build/**/*1892*",recursive=True)
print("R1892 candidates:")
for c in cands:
    if os.path.isfile(c):
        d=open(c,'rb').read()
        print(f"\n {c} ({len(d)}B)")
        print("   Vera rec16 @0x142:",read_name(d,0x142))
        # also dump all record names (stride 0x130, header at 0x140 + n*0x130)
