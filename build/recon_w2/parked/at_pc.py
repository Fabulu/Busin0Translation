import sys, struct, binascii, json
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
def u32(a): return struct.unpack_from("<I", ee, a)[0]
sec1=0x011C3D20; sec2=0x011CF540
pc=0x011CB113
rel=pc-sec1
print("pc rel=%05X  byte at pc..= %s"%(rel, binascii.hexlify(ee[pc:pc+24]).decode()))
op=(ee[pc]<<8)|ee[pc+1]
print("opcode at pc = %04X"%op)
# also show callstack: ctx+8 .. depth=3
ctx=0x017C8C58
print("callstack (depth3):")
for i in range(4):
    v=u32(ctx+8+i*4)
    print("  [%d] %08X rel=%05X"%(i,v, v-sec1 if sec1<=v<sec2 else -1))
# context bytes before pc
print("bytes [pc-16 .. pc+32]:")
print(binascii.hexlify(ee[pc-16:pc+32]).decode())
