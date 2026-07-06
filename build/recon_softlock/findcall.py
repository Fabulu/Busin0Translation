import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open('extracted/SLPM_653.78','rb').read()
def off(va): return va-0x100000+0x80
def va_at(o): return o+0x100000-0x80
# find function start of 0x13B340 by scanning back for 'jr ra; addiu sp,sp,+' epilogue or 'addiu sp,sp,-' with a jr ra before
# Instead: find all JAL targets and list jal X where X in range
lo=int(sys.argv[1],16); hi=int(sys.argv[2],16)
n=len(data)
for o in range(0x80, n-4,4):
    w=struct.unpack('<I',data[o:o+4])[0]
    if (w>>26)==3: # jal
        tgt=((w&0x3ffffff)<<2)
        # jal target in same 256MB region; PS2 uses pc upper bits
        tgt = (va_at(o)&0xf0000000)|tgt
        if lo<=tgt<=hi:
            print(f"jal 0x{tgt:08X} @ 0x{va_at(o):08X}")
