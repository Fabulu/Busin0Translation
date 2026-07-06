import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8')
# Array A Iris = [193,194,232,205] LE bytes. Search PACKDATA resources + EXE for this run.
iris=b''.join(struct.pack('<H',v) for v in [193,194,232,205])
iris_be=b''.join(struct.pack('>H',v) for v in [193,194,232,205])
basco=b''.join(struct.pack('<H',v) for v in [254,205,202,93])
print("LE iris bytes:",iris.hex())
roots=["C:/programmieren/wizardrytranslation/extracted/packdata_raw",
       "C:/programmieren/wizardrytranslation/extracted"]
files=[]
for r in roots:
    for dp,_,fn in os.walk(r):
        for f in fn:
            files.append(os.path.join(dp,f))
for f in files:
    try: d=open(f,'rb').read()
    except: continue
    for tag,pat in [("LE-iris",iris),("BE-iris",iris_be),("LE-basco",basco)]:
        j=d.find(pat)
        if j>=0:
            print(f"  {tag} @0x{j:X} in {os.path.relpath(f,'C:/programmieren/wizardrytranslation')}")
