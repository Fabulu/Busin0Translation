import sys, json, struct
sys.stdout.reconfigure(encoding='utf-8')
iso=open(r"C:/programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso","rb").read()
sig=bytes.fromhex("000000001fb800002000000000000000010000005c0e010040b80000")
idx=iso.find(sig)
orig=iso[idx:idx+0x20000]
orig_s1=orig[0x20:0x20+0x1FB8]
v99=open("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw","rb").read()
v99_s1=v99[0x20:0x20+0x1FB8]
diffs=[i for i in range(len(orig_s1)) if orig_s1[i]!=v99_s1[i]]
print("Section-1 diffs (v99 patched vs TRUE original JP ISO):", len(diffs))
runs=[]
for i in diffs:
    if runs and i<=runs[-1][1]+2: runs[-1][1]=i
    else: runs.append([i,i])
for a,b in runs:
    print("  rel %05X..%05X orig=%s v99=%s"%(a,b,orig_s1[a:b+1].hex(),v99_s1[a:b+1].hex()))
