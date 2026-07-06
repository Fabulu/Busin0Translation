import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from sec1_disasm import walk
HEADER=0x20
def sec1(p):
    d=open(p,'rb').read(); s2=struct.unpack_from('<I',d,0x18)[0]; return d[HEADER:s2]
JP='C:/programmieren/wizardrytranslation/extracted/packdata_raw/1196_type02.raw'
CUR='C:/programmieren/wizardrytranslation/build/packdata_resources/1196_type02.raw'
js=sec1(JP); cs=sec1(CUR)
jok,ji=walk(js); cok,ci=walk(cs)

# The 2B opcodes and the instruction immediately preceding each (the gate jump).
# Get the first 0x2B at 0x79C and dump full instruction + 16 bytes before
print("=== First portrait-emit 0x2B at 0x79C ===")
for tag,s,instrs in (('JP',js,ji),('CUR',cs,ci)):
    pc=0x79C
    # find preceding instr
    prev=max(p for p in instrs if p<pc)
    print(f"  {tag}: prev instr pc=0x{prev:X} op=0x{instrs[prev]:02X} bytes={s[prev:prev+12].hex()}")
    print(f"        2B bytes={s[pc:pc+16].hex()}")

# Compare ALL 0x2B bytes JP vs CUR
print("\n=== All 0x2B bytes identical? ===")
j2b={pc:bytes(js[pc:pc+16]) for pc in ji if ji[pc]==0x2B}
c2b={pc:bytes(cs[pc:pc+16]) for pc in ci if ci[pc]==0x2B}
print(f"  JP 2B count={len(j2b)} CUR 2B count={len(c2b)}")
mism=[pc for pc in (set(j2b)&set(c2b)) if j2b[pc]!=c2b[pc]]
print(f"  mismatched 2B instrs: {[hex(x) for x in mism]}")
# also check pcs only in one
print(f"  2B pcs only in JP: {[hex(x) for x in sorted(set(j2b)-set(c2b))]}")
print(f"  2B pcs only in CUR: {[hex(x) for x in sorted(set(c2b)-set(j2b))]}")

# Verify ALL 0x0C identical JP vs CUR
j0c={pc:bytes(js[pc:pc+6]) for pc in ji if ji[pc]==0x0C}
c0c={pc:bytes(cs[pc:pc+6]) for pc in ci if ci[pc]==0x0C}
mism0c=[pc for pc in (set(j0c)&set(c0c)) if j0c[pc]!=c0c[pc]]
print(f"\n  0x0C count JP={len(j0c)} CUR={len(c0c)}  mismatched={[hex(x) for x in mism0c]}")
print(f"  0x0C pcs only-JP={len(set(j0c)-set(c0c))} only-CUR={len(set(c0c)-set(j0c))}")

# Verify ALL 0x17/0x18 identical
for opc in (0x17,0x18):
    jo={pc:bytes(js[pc:pc+12]) for pc in ji if ji[pc]==opc}
    co={pc:bytes(cs[pc:pc+12]) for pc in ci if ci[pc]==opc}
    mm=[pc for pc in (set(jo)&set(co)) if jo[pc]!=co[pc]]
    print(f"  0x{opc:02X} count JP={len(jo)} CUR={len(co)} mismatched={[hex(x) for x in mm]} only-JP={len(set(jo)-set(co))} only-CUR={len(set(co)-set(jo))}")
