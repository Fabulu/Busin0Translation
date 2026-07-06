import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
DATA=open('extracted/SLPM_653.78','rb').read()
BASE_VA=0x100000; BASE_OFF=0x80
def va2off(va): return va-BASE_VA+BASE_OFF
def off2va(off): return off-BASE_OFF+BASE_VA

# find function start = first 'addiu $sp, $sp, -N' scanning backward; end = 'jr $ra' then delay slot
def find_func_end(va):
    off=va2off(va)
    i=off
    while i<BASE_OFF+0x3fdc80:
        w=struct.unpack('<I',DATA[i:i+4])[0]
        # jr $ra = 0x03e00008
        if w==0x03e00008:
            return off2va(i+4)  # include delay slot
        i+=4
    return None

def find_func_start(va):
    off=va2off(va)
    i=off
    while i>BASE_OFF:
        w=struct.unpack('<I',DATA[i:i+4])[0]
        # addiu $sp,$sp,-N : op=001001 rs=29 rt=29 imm negative
        if (w>>26)==9 and ((w>>21)&0x1f)==29 and ((w>>16)&0x1f)==29:
            imm=w&0xffff
            if imm>=0x8000:  # negative
                return off2va(i)
        # also jr $ra of previous function => start is next
        if w==0x03e00008 and i<off-4:
            return off2va(i+8)
        i-=4
    return None

for va in sys.argv[1:]:
    v=int(va,16)
    s=find_func_start(v); e=find_func_end(v)
    print(f"VA {hex(v)} -> func start {hex(s) if s else None} end {hex(e) if e else None}")
