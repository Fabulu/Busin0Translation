import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open('extracted/SLPM_653.78','rb').read()
def off(va): return va-0x100000+0x80
va=int(sys.argv[1],16); n=int(sys.argv[2])
for i in range(n):
    w=struct.unpack('<I',data[off(va+i*4):off(va+i*4)+4])[0]
    print(f"[{i}] 0x{va+i*4:08X} -> 0x{w:08X}")
