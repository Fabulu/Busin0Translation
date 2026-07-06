import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
# EXE file = vaddr - 0x100000 + 0x80  (per assignment: file=vaddr-0x100000+0x80)
exe = None
import glob, os
for p in [r"C:/programmieren/wizardrytranslation/build/SLPM_653.78",
          r"C:/programmieren/wizardrytranslation/SLPM_653.78"]:
    if os.path.exists(p):
        exe=p; break
if not exe:
    cands = glob.glob(r"C:/programmieren/wizardrytranslation/**/SLPM_653.78", recursive=True)
    print("candidates:", cands[:10])
    exe = cands[0] if cands else None
print("EXE:", exe)
if exe:
    data=open(exe,"rb").read()
    print("size",len(data))
