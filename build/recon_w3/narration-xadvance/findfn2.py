import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
D=open(EXE,'rb').read()
def v2f(va): return va-0x100000+0x80
target=int(sys.argv[1],16)
for i in range(4000):
    a=target-i*4
    w=struct.unpack_from('<I',D,v2f(a))[0]
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
    if op==0x09 and rs==29 and rt==29 and (imm&0x8000):
        print(f"fn start {a:08x}: addiu sp,sp,{imm-0x10000}  (target {target:08x}, -{i*4} bytes)")
        break
