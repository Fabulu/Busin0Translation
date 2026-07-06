import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
data=open('extracted/SLPM_653.78','rb').read()
def va_at(o): return o+0x100000-0x80
tgt=int(sys.argv[1],16)
for o in range(0x80,len(data)-4,4):
    if struct.unpack('<I',data[o:o+4])[0]==tgt:
        print(f"0x{tgt:08X} appears @ VA 0x{va_at(o):08X}")
