import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
gs=open('build/recon_cine/extract/overflowbartalk__gs.bin','rb').read()
# PCSX2 GSDump format (newer): header then "regs" then packets. Hard to parse blindly.
# Instead scan for SCISSOR_1 (0x40) register values that look like a dialogue box.
# A GIFtag A+D packet: each entry is 16 bytes: data(8) + addr(8, low byte=reg).
# Scan whole file for addr byte 0x40 (SCISSOR_1) or 0x41 (SCISSOR_2) at 16-byte aligned A+D.
seen=set()
for i in range(0, len(gs)-16):
    reg=gs[i+8]
    if reg in (0x40,0x41) and gs[i+9]==0 and gs[i+10]==0 and gs[i+11]==0 and gs[i+12]==0 and gs[i+13]==0 and gs[i+14]==0 and gs[i+15]==0:
        d=struct.unpack_from('<Q',gs,i)[0]
        scax0=d&0x7ff; scax1=(d>>16)&0x7ff; scay0=(d>>32)&0x7ff; scay1=(d>>48)&0x7ff
        key=(scax0,scax1,scay0,scay1)
        if key not in seen and scax1>0 and scay1>0:
            seen.add(key)
            print('SCISSOR x[%d..%d] y[%d..%d] (w=%d h=%d)'%(scax0,scax1,scay0,scay1,scax1-scax0+1,scay1-scay0+1))
