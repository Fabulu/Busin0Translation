import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
ee=open(f'{BASE}/build/recon_portrait4/extract/request__ee.bin','rb').read()
# The RAM roster name run for Vera as LE u16: 11 01 0e 01 5d 00 e7 00
vera_le=struct.pack('<4H',273,270,93,231)
basco_le=struct.pack('<4H',254,205,202,93)  # バ ス コ ー = 254,205,202,93
# Count hits of vera_le across whole EE to see all copies
def hits(pat,lim=60):
    out=[];s=0
    while True:
        i=ee.find(pat,s)
        if i<0:break
        out.append(i);s=i+1
        if len(out)>lim:break
    return out
print('Vera LE-u16 name-run copies in EE:', ['0x%x'%h for h in hits(vera_le)])
# Now check R2654 subs for a roster containing バスコー (Basco) - search the build R2654 raw
r2654=open(f'{BASE}/build/packdata_resources/2654_type44.raw','rb').read()
prist=open(f'{BASE}/extracted/packdata_raw/2654_type44.raw','rb').read()
# Basco BE u16 run in R2654
basco_be=struct.pack('>4H',254,205,202,93)
freesia_be=struct.pack('>5H',220,232,232,245,193)  # フ リ ー ジ ア =220,232,93,245,193? guess
def hits_in(buf,pat,lim=20):
    out=[];s=0
    while True:
        i=buf.find(pat,s)
        if i<0:break
        out.append(i);s=i+1
        if len(out)>lim:break
    return out
print('Basco BE-u16 in BUILD R2654:', ['0x%x'%h for h in hits_in(r2654,basco_be)])
print('Basco BE-u16 in PRISTINE R2654:', ['0x%x'%h for h in hits_in(prist,basco_be)])
# Dump R2654 header subs to see which has the roster
NSUBS=44
print('\nR2654 (pristine) subs:')
for i in range(NSUBS):
    sub,size,off,z=struct.unpack_from('<4I',prist,i*16)
    print(f'  hdr[{i}] sub={sub} size=0x{size:x} off=0x{off:x}')
