import sys, struct
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
CUR='C:/programmieren/wizardrytranslation/build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__ee.bin'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
cur=open(CUR,'rb').read(); ref=open(REF,'rb').read()
# The flag tables are at 0x565090..0x565150. The 433-entry scene-var array (SET 0x301E50)
# is likely a nearby BSS region. Search for a region of 433 contiguous u8/u32 near the flag tables
# that differs between CUR and REF in a way consistent with per-scene booleans.
# Just dump the region 0x565000..0x566000 diff to locate the scene-var array.
base=0x565000; size=0x1000
ca=np.frombuffer(cur[base:base+size],dtype=np.uint8)
ra=np.frombuffer(ref[base:base+size],dtype=np.uint8)
diff=np.nonzero(ca!=ra)[0]
print(f"region 0x{base:X}..0x{base+size:X}: {len(diff)} differing bytes")
# group into ranges
if len(diff):
    runs=[]; s=diff[0]; p=diff[0]
    for x in diff[1:]:
        if x==p+1: p=x
        else: runs.append((s,p)); s=x; p=x
    runs.append((s,p))
    for s,e in runs[:30]:
        print(f"  0x{base+s:08X}..0x{base+e:08X} ({e-s+1}B) CUR={cur[base+s:base+e+1][:12].hex()} REF={ref[base+s:base+e+1][:12].hex()}")
