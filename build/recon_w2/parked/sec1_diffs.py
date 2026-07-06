import sys, json, binascii
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
res=0x011C3D00
ram=ee[res:res+0x1FB8+0x20]
pre=open("C:/programmieren/wizardrytranslation/build/packdata_resources_backup/1197_type02.raw","rb").read()
s_ram=ram[0x20:0x20+0x1FB8]; s_pre=pre[0x20:0x20+0x1FB8]
diffs=[i for i in range(len(s_ram)) if s_ram[i]!=s_pre[i]]
# group consecutive diffs into runs
runs=[]
for i in diffs:
    if runs and i<=runs[-1][1]+4: runs[-1][1]=i
    else: runs.append([i,i])
print("diff runs (rel to sec1):")
for a,b in runs:
    print("  rel %05X..%05X : v99=%s  pre=%s"%(a,b, s_ram[a:b+1].hex(), s_pre[a:b+1].hex()))
# For each run, find the enclosing opcode by walking from a safe start
