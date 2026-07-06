import sys, json
sys.stdout.reconfigure(encoding='utf-8')
# Decode pre vs v99 around the jump to see if pre also had a 0x07 at 0x614 region (to compare structure)
ee=open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
res=0x011C3D00; sec1=res+0x20
s=ee[sec1:sec1+0x1FB8]
pre=open("C:/programmieren/wizardrytranslation/build/packdata_resources_backup/1197_type02.raw","rb").read()[0x20:0x20+0x1FB8]
opt=json.load(open(r"C:/programmieren/wizardrytranslation/build/recon_v85/exe-interpreter/opcode_table_v85.json"))["opcodes"]
def oplen(op):
    info=opt.get("0x%02X"%op); return info["bytes"] if info else 2
# Is the 0x06@0x5D0 byte-identical in pre except target? show both full
print("0x06 @ 5D0:")
print("  pre:", pre[0x5D0:0x5D0+14].hex())
print("  v99:", s[0x5D0:0x5D0+14].hex())
# In pristine, what is at 0x0614? and what jumps to 0x08AB region?
print("\npristine @0x0614:", pre[0x614:0x614+14].hex())
print("v99      @0x0614:", s[0x614:0x614+14].hex())
print("\npristine @0x08AB:", pre[0x8AB:0x8AB+14].hex())
print("v99      @0x08AB:", s[0x8AB:0x8AB+14].hex())
# Count how many opcodes reference 0x08AB vs 0x0614 as targets in pristine
import struct
def scan_targets(buf):
    a=0; refs={}
    while a<len(buf)-1:
        op=(buf[a]<<8)|buf[a+1]; ln=oplen(op)
        if op in (0x06,0x07) and a+14<=len(buf):
            tgt=struct.unpack_from(">I",buf,a+10)[0]
            refs.setdefault(tgt,[]).append((a,op))
        elif op in (0x08,0x0B) and a+6<=len(buf):
            tgt=struct.unpack_from(">I",buf,a+2)[0]
            refs.setdefault(tgt,[]).append((a,op))
        a+=ln
    return refs
pr=scan_targets(pre); vr=scan_targets(s)
print("\npristine refs to 0x08AB:", pr.get(0x08AB))
print("pristine refs to 0x0614:", pr.get(0x0614))
print("v99 refs to 0x08AB:", vr.get(0x08AB))
print("v99 refs to 0x0614:", vr.get(0x0614))
