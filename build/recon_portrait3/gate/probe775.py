import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from sec1_disasm import walk

JP='C:/programmieren/wizardrytranslation/extracted/packdata_raw/1196_type02.raw'
CUR='C:/programmieren/wizardrytranslation/build/packdata_resources/1196_type02.raw'
HEADER=0x20
def sec1(p):
    d=open(p,'rb').read()
    s2=struct.unpack_from('<I',d,0x18)[0]
    return d[HEADER:s2]
js=sec1(JP); cs=sec1(CUR)

# context around 0x775
for tag,s in (('JP',js),('CUR',cs)):
    print(f"{tag} sec1[0x760:0x790]:", s[0x760:0x790].hex())

# Is 0x775 a reachable instruction in the walk?
jok,ji=walk(js); cok,ci=walk(cs)
print("JP walk ok",jok,"ninstr",len(ji),"| CUR walk ok",cok,"ninstr",len(ci))
print("0x775 in JP instrs?", 0x775 in ji, "-> op", hex(ji.get(0x775,-1)))
print("0x775 in CUR instrs?", 0x775 in ci, "-> op", hex(ci.get(0x775,-1)))
# nearest instr boundaries around 0x775
jnear=[pc for pc in sorted(ji) if 0x760<=pc<=0x790]
cnear=[pc for pc in sorted(ci) if 0x760<=pc<=0x790]
print("JP instr pcs near:", [hex(x) for x in jnear], [hex(ji[x]) for x in jnear])
print("CUR instr pcs near:", [hex(x) for x in cnear], [hex(ci[x]) for x in cnear])

# Show the instruction that CONTAINS 0x775 in each
def containing(instrs, off):
    prev=None
    for pc in sorted(instrs):
        if pc<=off: prev=pc
        else: break
    return prev
jc=containing(ji,0x775); cc=containing(ci,0x775)
print(f"JP: 0x775 inside instr pc=0x{jc:X} op=0x{ji[jc]:02X} bytes={js[jc:jc+14].hex()}")
print(f"CUR: 0x775 inside instr pc=0x{cc:X} op=0x{ci[cc]:02X} bytes={cs[cc:cc+14].hex()}")

# Where does the first OPCODE-level walk divergence happen?
allpc=sorted(set(ji)|set(ci))
for pc in allpc:
    if ji.get(pc)!=ci.get(pc):
        print(f"FIRST walk divergence at pc=0x{pc:X}: JP op={ji.get(pc)} CUR op={ci.get(pc)}")
        break
else:
    print("Walks produce IDENTICAL opcode map (same pcs, same opcodes) despite byte diffs")
