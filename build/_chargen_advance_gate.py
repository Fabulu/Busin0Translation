import struct
exec(open(r"C:\programmieren\wizardrytranslation\build\_chargen_disasm.py").read().split("import sys")[0])

print("=== ADVANCE region 0x3079C0..0x307A00 (PRISTINE vs PATCHED) ===")
for va in range(0x3079C0, 0x307A04, 4):
    off=va2off(va)
    pw=w(pri,off); xw=w(pat,off)
    flag = "" if pw==xw else "  <<< PATCHED DIFFERS"
    print(f"  0x{va:06X}: pri={pw:08X} {disasm(pw,va):28s} | pat={xw:08X}{flag}")

# check overall: does patched differ ANYWHERE in 0x307510..0x307A50?
print("\n=== diff scan whole function 0x307510..0x307A50 ===")
ndiff=0
for va in range(0x307510, 0x307A50, 4):
    off=va2off(va)
    if w(pri,off)!=w(pat,off):
        ndiff+=1
        print(f"  DIFF 0x{va:06X}: pri={w(pri,off):08X} pat={w(pat,off):08X}")
if ndiff==0:
    print("  NO differences -> this function is PRISTINE in patched EXE (untouched, good patch target)")

# ---- GATE HUNT: 0x4FED18 ----
print("\n=== 0x4FED18 gate hunt (lui 0x50 / 0x4F + load off -0x12E8/0xED18) ===")
# scan whole text for lui rX,0x50 (0x3C..0050) or lui rX,0x4F (0x3C..004F)
# then within next 8 instrs a load (op 0x20-0x25/0x23) with imm == 0xED18 (for 0x4F) or 0xED18-0x10000=-0x12E8 => imm field 0xED18 too actually
# For lui 0x50 base, real addr 0x500000 + signed_off. 0x4FED18 = 0x500000 - 0x12E8 -> imm 0xED18 (since signed 0xED18 = -0x12E8). Same imm bytes!
def is_load(word):
    return (word>>26) in (0x20,0x21,0x23,0x24,0x25)
hits=[]
for off in range(OFF_LO, OFF_HI-4, 4):
    word=w(pri,off)
    if (word>>26)==0x0F:  # lui
        imm=word&0xFFFF; rt=(word>>16)&0x1F
        if imm in (0x0050,0x004F):
            base_va=off2va(off)
            for k in range(1,9):
                w2=w(pri,off+4*k)
                if is_load(w2):
                    rs=(w2>>21)&0x1F; loff=w2&0xFFFF
                    if rs==rt and (loff==0xED18):
                        hits.append((base_va, off2va(off+4*k), imm))
for bva, lva, imm in hits:
    print(f"  lui r,0x{imm:04X} @0x{bva:06X} + load @0x{lva:06X}  (addr 0x4FED18) {'[near chargen renderer!]' if 0x307000<=bva<=0x30A000 else ''}")
if not hits:
    print("  no direct 0x4FED18 lui+load pairs found in pristine text")
