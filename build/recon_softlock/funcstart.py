import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open('extracted/SLPM_653.78','rb').read()
def off(va): return va-0x100000+0x80
va=int(sys.argv[1],16)
# scan back for 'addiu sp,sp,-X' preceded by jr ra
o=off(va)
for i in range(0,4000,4):
    w=struct.unpack('<I',data[o-i:o-i+4])[0]
    # addiu sp,sp,neg : op=9 rs=29 rt=29 imm high bit set
    if (w>>26)==9 and ((w>>21)&0x1f)==29 and ((w>>16)&0x1f)==29 and (w&0x8000):
        # check prev word is jr ra (0x03e00008) possibly with delay slot
        for j in (4,8):
            pw=struct.unpack('<I',data[o-i-j:o-i-j+4])[0]
            if pw==0x03e00008:
                print(f"func start 0x{va-i:08X}  (prologue addiu sp,-0x{(0x10000-(w&0xffff)):X})")
                sys.exit()
print("not found cleanly; nearest addiu sp candidates:")
for i in range(0,4000,4):
    w=struct.unpack('<I',data[o-i:o-i+4])[0]
    if (w>>26)==9 and ((w>>21)&0x1f)==29 and ((w>>16)&0x1f)==29 and (w&0x8000):
        print(f"  0x{va-i:08X} addiu sp,-0x{(0x10000-(w&0xffff)):X}"); 
        if i>200: break
