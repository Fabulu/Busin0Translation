import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
P='build/recon_portrait4/extract/nshadymanand4linesinsteadof3__gs.bin'
d=open(P,'rb').read()
print("filesize",len(d))
print("first 64 bytes hex:")
print(d[:64].hex())
# header 509 bytes per reconstruct. Look for GS register dump / DISPLAY regs maybe in header.
# Print header as bytes
hdr=d[:509]
# search for ascii
import re
for m in re.finditer(rb'[ -~]{4,}', hdr):
    print("  str@%d: %r"%(m.start(),m.group()))
