import sys, json
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
res=0x011C3D00; sec1=res+0x20
s=ee[sec1:sec1+0x1FB8]
pre=open("C:/programmieren/wizardrytranslation/build/packdata_resources_backup/1197_type02.raw","rb").read()[0x20:0x20+0x1FB8]
sec1_size=0x1FB8
def oplen(op):
    info=opt.get("0x%02X"%op); return (info["bytes"],info["note"]) if info else (2,"??")
def decode_at(buf,off,n=6,label=""):
    print(f"  [{label}] decode from {off:#06x}:")
    a=off
    for _ in range(n):
        if a>=len(buf)-1: break
        op=(buf[a]<<8)|buf[a+1]; ln,note=oplen(op)
        print("    %05X: op=%02X %-40s %s"%(a,op,note,buf[a:a+ln].hex()))
        a+=ln
print("opcode 0x06 @ 0x5D0:")
print("  v99 target=0x%04X  pre target=0x%04X  sec1_size=0x%04X"%(0x0614,0x08AB,sec1_size))
print("  both < sec1_size? v99:",0x0614<sec1_size," pre:",0x08AB<sec1_size)
print("\n--- pristine target 0x08AB (where the original jumps) ---")
decode_at(pre,0x08AB,8,"pre@08AB")
print("\n--- v99 (injected) target 0x0614 (where it NOW jumps) ---")
decode_at(s,0x0614,8,"v99@0614")
print("\n--- context: opcode just BEFORE 0x5D0 to confirm this is in request menu ---")
decode_at(s,0x05B8,8,"before")
