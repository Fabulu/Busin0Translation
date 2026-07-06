import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
gs=open('build/recon_cine/extract/overflowbartalk__gs.bin','rb').read()
print('gs size', len(gs), hex(len(gs)))
print('head', gs[:16].hex())
# PCSX2 GSdump: try to find FRAME/DISPLAY/XYOFFSET via scanning GS reg writes.
# Heuristic: search for known magic
print('first 64 bytes:', gs[:64].hex())
