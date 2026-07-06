import struct,glob,os
# find patched exe output
cands=glob.glob('build/**/SLPM_653.78*',recursive=True)+glob.glob('build/*SLPM*')+glob.glob('extracted/*patched*')
# patch_exe.py default output:
import subprocess
# Just re-run reading where patch_exe writes. Check common names.
for p in ['build/SLPM_653.78','build/patched_SLPM_653.78','extracted/SLPM_653.78_patched']:
    if os.path.exists(p): print("found",p)
print("candidates:",cands)
