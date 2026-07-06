import sys, struct, json, binascii
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
sec1=0x011C3D20
def show(pc, n=12, label=""):
    print(f"=== {label} pc=rel {pc-sec1:#06x} ===")
    a=pc
    for _ in range(n):
        op=(ee[a]<<8)|ee[a+1]
        key="0x%02X"%op if op<0x100 else "0x%04X"%op
        info=opt.get(key) or opt.get("0x%02X"%op)
        ln = info["bytes"] if info else 2
        note = info["note"] if info else "??"
        print("  rel %05X: op=%04X len=%d  %s  bytes=%s"%(a-sec1, op, ln, note, binascii.hexlify(ee[a:a+ln]).decode()))
        a+=ln
show(sec1+0x1EF4, 10, "cand A (011C5C14)")
show(sec1+0x73F3, 10, "cand B (011CB113)")
