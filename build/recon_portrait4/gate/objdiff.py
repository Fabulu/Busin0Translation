import sys, struct
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
present=open(f'{E2}/Firstdialogue__ee.bin','rb').read()
nshady=open(f'{E}/nshadymanand4linesinsteadof3__ee.bin','rb').read()
# Focus on the descriptor / scene-object BSS region. The descriptor array at 0x55E5A0 stride480,
# slot table 0x542748, CG ptr BSS 0x509F80. Diff a wide BSS window 0x540000..0x570000
base=0x540000; end=0x570000
pa=np.frombuffer(present[base:end],dtype=np.uint8)
na=np.frombuffer(nshady[base:end],dtype=np.uint8)
diff=np.nonzero(pa!=na)[0]
print(f"region 0x{base:X}..0x{end:X}: {len(diff)} differing bytes (PRESENT vs nshadyman)")
# group
if len(diff):
    runs=[]; s=diff[0]; p=diff[0]
    for x in diff[1:]:
        if x==p+1: p=x
        else: runs.append((s,p)); s=x; p=x
    runs.append((s,p))
    print(f"  {len(runs)} runs:")
    for s,e in runs[:60]:
        print(f"    0x{base+s:08X}..0x{base+e:08X} ({e-s+1}B) P={present[base+s:base+e+1][:16].hex()} N={nshady[base+s:base+e+1][:16].hex()}")
