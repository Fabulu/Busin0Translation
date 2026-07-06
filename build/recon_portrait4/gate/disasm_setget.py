import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
d=open(EXE,'rb').read()
# file = vaddr - 0x100000 + 0x80
def f2(va): return va-0x100000+0x80
def disasm_range(va,n):
    off=f2(va)
    for i in range(n):
        w=struct.unpack_from('<I',d,off+i*4)[0]
        print(f"  0x{va+i*4:08X}: {w:08X}  {decode(w)}")
def decode(w):
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; imm=w&0xFFFF
    simm=imm-0x10000 if imm&0x8000 else imm
    if op==0: 
        fn=w&0x3F
        names={0x20:'add',0x21:'addu',0x22:'sub',0x23:'subu',0x24:'and',0x25:'or',0x2A:'slt',0x2B:'sltu',0x00:'sll',0x02:'srl',0x03:'sra',0x08:'jr',0x09:'jalr'}
        return f"{names.get(fn,'spec%02x'%fn)} r{rd},r{rs},r{rt}"
    names={0x23:'lw',0x2B:'sw',0x20:'lb',0x24:'lbu',0x21:'lh',0x25:'lhu',0x28:'sb',0x29:'sh',0x0F:'lui',0x09:'addiu',0x0C:'andi',0x0D:'ori',0x08:'addi',0x0A:'slti',0x04:'beq',0x05:'bne',0x03:'jal',0x02:'j'}
    nm=names.get(op,'op%02x'%op)
    if op in (0x23,0x2B,0x20,0x24,0x21,0x25,0x28,0x29): return f"{nm} r{rt},{simm}(r{rs})"
    if op==0x0F: return f"lui r{rt},0x{imm:04X}"
    if op in (0x09,0x0C,0x0D,0x08,0x0A): return f"{nm} r{rt},r{rs},{simm}"
    if op in (0x04,0x05): return f"{nm} r{rs},r{rt},0x{imm:04X}"
    if op in (0x03,0x02): return f"{nm} 0x{((w&0x3FFFFFF)<<2):08X}"
    return nm
print("=== GET 0x301E10 (scene-var read) ===")
disasm_range(0x301E10,18)
print("=== SET 0x301E50 (scene-var write) ===")
disasm_range(0x301E50,18)
print("=== COND_EVAL 0x3022F0 (head) ===")
disasm_range(0x3022F0,12)
