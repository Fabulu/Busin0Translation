import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def cnt(path):
    d=open(path,'rb').read()
    from collections import Counter
    c=Counter()
    for i in range(0,len(d)-1,2):
        v=struct.unpack_from('>H',d,i)[0]
        if v>=0xFF00:
            c[v]+=1
    return c
pristine=r"C:/programmieren/wizardrytranslation/extracted/packdata_raw/1197_type02.raw"
patched =r"C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw"
for label,p in [("PRISTINE JP",pristine),("PATCHED EN",patched)]:
    c=cnt(p)
    print(f"\n{label} ({p.split('/')[-1]}): control-code (>=0xFF00) freq:")
    for v in sorted(c):
        print(f"  0x{v:04X}: {c[v]}")
