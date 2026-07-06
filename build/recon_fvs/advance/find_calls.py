import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
data=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
target=int(sys.argv[1],16)
# JAL encodes (target>>2)&0x3FFFFFF, opcode 0x0C
tgt_field=(target>>2)&0x03FFFFFF
jal_word=(0x03<<26)|tgt_field
for off in range(0x80, len(data)-3, 4):
    w=struct.unpack_from('<I',data,off)[0]
    if w==jal_word:
        print(f"JAL 0x{target:08X} from VA 0x{f2v(off):08X} (file 0x{off:06X})")
