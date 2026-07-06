import struct
ee=open('_q7/chargen_ee.bin','rb').read()
def dump(base, n=80):
    print(f"--- cells at 0x{base:08X} ---")
    s=''
    for i in range(n):
        v=struct.unpack_from('<H',ee,base+i*2)[0]
        if v==0xFFFF:
            print(f"[{i}] 0xFFFF TERM"); break
        hi=(v>>8)&0xFF; lo=v&0xFF
        ch=chr(hi+32) if 0x20<=hi+32<0x7f else '?'
        s+=ch
        if i<24: print(f"[{i}] 0x{v:04X} hi={hi:02X} lo={lo:02X} -> '{ch}'")
    print("STR:", repr(s))
# Lives... box. Back up to find array start (look backward for FFFF or struct head)
base=0xe148b2
# scan backward for 0xFFFF terminator to find this string's array start
p=base
for back in range(0, 400, 2):
    v=struct.unpack_from('<H',ee,base-back)[0]
    if v==0xFFFF:
        print("array start after FFFF at", hex(base-back+2), "(FFFF at", hex(base-back),")")
        dump(base-back+2, 120)
        break
