import sys, struct
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

CUR='C:/programmieren/wizardrytranslation/build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__ee.bin'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
def load(p): return open(p,'rb').read()
cur=load(CUR); ref=load(REF)

# 433-entry scene-var array (SET 0x301E50). Find its base.
# The prompt: opcode 0x17/0x18 -> FLAG_TEST writes a scene-var (433-entry array).
# We don't have the base addr directly. But the channel-flag tables are at 0x565090/D0/110.
# param2=0x565090, param1=0x5650D0, param0=0x565110. Each spans... param2->param1 = 0x40 (64 bytes=16 words=512 bits).
# So each table is 64 bytes = 512 bits? But we saw param0 bits up to 568 -> needs >512 bits => tables larger.
# Let's measure: 0x5650D0-0x565090=0x40 (64B), 0x565110-0x5650D0=0x40 (64B). So 64 bytes each = 512 bits.
# But bit 568 set in param0 (0x565110) would be at 0x565110+71 bytes -> beyond next table. Overlap!
# => Layout order in MEMORY is param2(0x565090) < param1(0x5650D0) < param0(0x565110), each 64B,
#    BUT param0 is the LAST so it can extend. Re-examine which table is which.
# Print raw 0x60 bytes from each base.
for name,base in (('0x565090',0x565090),('0x5650D0',0x5650D0),('0x565110',0x565110)):
    cw=struct.unpack_from('<24I',cur,base)
    rw=struct.unpack_from('<24I',ref,base)
    print(f"--- {name} (24 words) ---")
    diffwords=[i for i in range(24) if cw[i]!=rw[i]]
    print(f"  diff word idxs vs ref: {diffwords}")
    for i in diffwords:
        cb=[i*32+b for b in range(32) if cw[i]&(1<<b)]
        rb=[i*32+b for b in range(32) if rw[i]&(1<<b)]
        only_cur=sorted(set(cb)-set(rb)); only_ref=sorted(set(rb)-set(cb))
        print(f"    word[{i}]: CUR=0x{cw[i]:08X} REF=0x{rw[i]:08X}  set-only-in-CUR={only_cur} set-only-in-REF={only_ref}")
