import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EE='build/recon_portrait4/extract/request__ee.bin'
ee=open(EE,'rb').read()
def rd32(a): return struct.unpack_from('<I',ee,a)[0]
# Find the resident R1197 section-1 in EE RAM. Read the built R1197 sec1 first 64 bytes signature.
import struct as S
def sec1(path):
    d=open(path,'rb').read(); s2=S.unpack_from('<I',d,0x18)[0]; return d[0x20:s2]
c1196=sec1('build/packdata_resources/1196_type02.raw')
c1197=sec1('build/packdata_resources/1197_type02.raw')
# Search EE for these sec1 blobs (find where resource is resident)
for rid,blob in ((1196,c1196),(1197,c1197)):
    sig=blob[:48]
    idx=ee.find(sig)
    print(f"R{rid} sec1 sig found at EE 0x{idx:08X}" if idx>=0 else f"R{rid} sec1 NOT resident")
    # also search the full sec2 first 48 bytes? skip
# Try to find interpreter PC: scan for pointers into a resident sec1 region
