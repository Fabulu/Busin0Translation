import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
import rabbitizer
exe=open("extracted/SLPM_653.78","rb").read()
def f(va): return va-0x100000+0x80
# The FontDispSet function takes glyph_id, computes base+glyph_id*50, writes field0=page_index.
# Find functions that do the *50 multiply (sll*2;addu;sll*2;addu;sll*1 pattern) + sh to offset 0.
# Search for the *25*2 idiom near gp-26852 load. We already know readers; find sh ...,0(reg) after struct addr compute.
# Simpler: list all functions calling 0x30B770 (page check) or referencing gp-26852 for WRITE via computed ptr.
# Find the 'FontDispSet' setter: scan for sequence ' sh X,0(Y) ' where Y derived from gp-26852.
# Brute: print disasm of region 0x30AE20..0x30B770 (the tile setup funcs from notes: 0x30AE20 clears array, 0x306E20 per-tile)
def dis(s,e,label=""):
    print(f"--- {label} 0x{s:X}-0x{e:X} ---")
    for va in range(s,e,4):
        raw=struct.unpack_from("<I",exe,f(va))[0]
        ins=rabbitizer.Instruction(raw); ins.vram=va
        print(f"0x{va:08X}: {raw:08X} {ins.disassemble()}")
dis(0x30AE20,0x30AF00,"0x30AE20 (clears tile array?)")
