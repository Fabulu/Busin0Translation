import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S

pat = open('build/patched_type2/1197_type02.raw','rb').read()
pri = open('extracted/packdata_raw/1197_type02.raw','rb').read()

okp,ip,s1p,off_p = S.walk_resource(pat)
okq,iq,s1q,off_q = S.walk_resource(pri)
print("sec2_off patched=0x%x pristine=0x%x"%(off_p,off_q))
print("sec1 len patched=%d pristine=%d"%(len(s1p),len(s1q)))
print("total file patched=%d pristine=%d"%(len(pat),len(pri)))

# Walk-instruction set equal?
print("PC set equal:", set(ip.keys())==set(iq.keys()))
# opcode at each pc equal?
opdiff=[pc for pc in ip if iq.get(pc)!=ip[pc]]
print("opcode-at-pc diffs:", len(opdiff))

# Now diff sec1 bytes per opcode. For each reachable instr, compare operand bytes
# but ALLOW differences only in 0x04 (+2 off,+6 cnt) and 0x14 (+6 off,+10 cnt) remap fields.
def beu32(b,o): return struct.unpack_from(">I",b,o)[0]
def beu16(b,o): return struct.unpack_from(">H",b,o)[0]

LEN=S.LENB
unexpected=[]
remap04=0
remap14=0
for pc in sorted(ip):
    op=ip[pc]
    ln=LEN[op]
    a=s1p[pc:pc+ln]
    b=s1q[pc:pc+ln]
    if a==b: continue
    # differences exist; classify
    if op==0x04:
        # allowed: bytes +2..+10 (off u32, cnt u32). check rest identical
        ap=s1p[pc:pc+2]+s1p[pc+10:pc+ln]
        bp=s1q[pc:pc+2]+s1q[pc+10:pc+ln]
        if ap==bp: remap04+=1
        else: unexpected.append((pc,op,'04-nonremap',a.hex(),b.hex()))
    elif op==0x14:
        # allowed: +6 off u32, +10 cnt u32. param@+2 u16, +4 s16 must match
        ap=s1p[pc:pc+6]+s1p[pc+14:pc+ln]
        bp=s1q[pc:pc+6]+s1q[pc+14:pc+ln]
        if ap==bp: remap14+=1
        else: unexpected.append((pc,op,'14-nonremap',a.hex(),b.hex()))
    else:
        unexpected.append((pc,op,'OTHER',a.hex(),b.hex()))

print("remapped 0x04:",remap04," remapped 0x14:",remap14)
print("UNEXPECTED sec1 opcode diffs:", len(unexpected))
for u in unexpected[:50]:
    print("  pc=0x%x op=0x%02x %s\n     patched=%s\n     pristine=%s"%u)
