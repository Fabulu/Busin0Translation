import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
DUMPS={
 'PRESENT':   f'{E2}/Firstdialogue__ee.bin',
 'nshadyman': f'{E}/nshadymanand4linesinsteadof3__ee.bin',
 'nosister':  f'{E}/nosister__ee.bin',
 'ladyknight':f'{E}/ladyknightnoportrait__ee.bin',
}
def load(p): return open(p,'rb').read()
bufs={k:load(v) for k,v in DUMPS.items()}
# Interpreter state: dispatcher at va 0x2F3230. Script PC is likely held in a global.
# Search around gp for a value in sec1 range (0..0x8000). gp=0x504FF0. Dump gp-relative globals
# that could be the script PC + the "current portrait/CG id pending" var.
# Instead: dump a window of likely-interpreter-state BSS. The 0x2B handler 0x2F5300 alloc 0x1B7200 -> table 0x542748.
# The pending CG id requested by 0x2B may sit in a global. Let's scan 0x504000..0x50A000 for differences
# between PRESENT and nshadyman that are small ints (candidate "active portrait id").
import numpy as np
base=0x504000; end=0x50A000
pa=np.frombuffer(bufs['PRESENT'][base:end],dtype=np.uint8)
na=np.frombuffer(bufs['nshadyman'][base:end],dtype=np.uint8)
diff=np.nonzero(pa!=na)[0]
print(f"globals 0x{base:X}..0x{end:X}: {len(diff)} diff bytes PRESENT vs nshadyman")
runs=[]
if len(diff):
    s=diff[0]; p=diff[0]
    for x in diff[1:]:
        if x<=p+3: p=x
        else: runs.append((s,p)); s=x; p=x
    runs.append((s,p))
for s,e in runs:
    a=base+s
    print(f"  0x{a:08X}..0x{base+e:08X}: P={bufs['PRESENT'][a:base+e+1][:12].hex()} N={bufs['nshadyman'][a:base+e+1][:12].hex()}")
