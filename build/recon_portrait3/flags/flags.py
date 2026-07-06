import sys, struct
sys.stdout.reconfigure(encoding='utf-8')

CUR = r"C:/programmieren/wizardrytranslation/build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__ee.bin"
REF = r"C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin"

# Channel-flag tables (RAM vaddr == fileoff in eeMemory.bin)
TABLES = {
    "0x565090 (param2)": 0x565090,
    "0x5650D0 (param1)": 0x5650D0,
    "0x565110 (param0)": 0x565110,
}
CGSLOT = 0x509F80

def load(p):
    with open(p,'rb') as f:
        return f.read()

cur = load(CUR)
ref = load(REF)

def dump_table(buf, base, label, words=32):
    # how many u32 in this bitmap? idx>>5 up to 433 entries -> ceil(433/32)=14 words
    print(f"  {label} base=0x{base:08X}")
    anybits=False
    for w in range(words):
        v = struct.unpack_from('<I', buf, base + w*4)[0]
        if v:
            anybits=True
            bits = [w*32 + b for b in range(32) if v & (1<<b)]
            print(f"    word[{w}] off+0x{w*4:02X} = 0x{v:08X}  set-indices={bits}")
    if not anybits:
        print("    (all zero)")

for name, addr in TABLES.items():
    print(f"=== CURRENT {name} ===")
    dump_table(cur, addr, name)
    print(f"=== REFERENCE {name} ===")
    dump_table(ref, addr, name)
    print()

# CG slot pointer
cur_slot = struct.unpack_from('<I', cur, CGSLOT)[0]
ref_slot = struct.unpack_from('<I', ref, CGSLOT)[0]
print(f"CG slot ptr BSS 0x{CGSLOT:08X}:")
print(f"  CURRENT = 0x{cur_slot:08X}")
print(f"  REFERENCE = 0x{ref_slot:08X}")

# Dump a small region around the slot for context (8 ptrs)
print("CG slot region (CURRENT):")
for i in range(8):
    v = struct.unpack_from('<I', cur, CGSLOT + i*4)[0]
    print(f"    0x{CGSLOT+i*4:08X} = 0x{v:08X}")
print("CG slot region (REFERENCE):")
for i in range(8):
    v = struct.unpack_from('<I', ref, CGSLOT + i*4)[0]
    print(f"    0x{CGSLOT+i*4:08X} = 0x{v:08X}")
