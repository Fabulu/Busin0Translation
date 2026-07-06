import sys, struct, json, binascii
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
sec1=0x011C3D20
def oplen(op):
    info=opt.get("0x%02X"%op)
    return (info["bytes"], info["note"]) if info else (2,"??")
def walk(rel, n=40, label=""):
    print(f"=== {label} from rel {rel:#06x} ===")
    a=sec1+rel
    for _ in range(n):
        r=a-sec1
        op=(ee[a]<<8)|ee[a+1]
        ln,note=oplen(op)
        b=binascii.hexlify(ee[a:a+ln]).decode()
        # decode jump targets for 0x06/0x07/0x08/0x0B/0x11/0x12
        extra=""
        if op in (0x06,0x07):
            # COND JUMP: 14 bytes. target likely last u32? format 0007 013f 00400000 40000000 1F16  -> target u16 at end (2 bytes)
            tgt=(ee[a+12]<<8)|ee[a+13]
            extra="-> rel %05X"%tgt
        elif op in (0x08,0x0B):
            tgt=(ee[a+4]<<8)|ee[a+5]
            extra="-> rel %05X"%tgt
        print("  rel %05X: op=%02X len=%2d %-30s %s %s"%(r,op,ln,note,b,extra))
        a+=ln
walk(0x1EF4, 30, "live PC")
