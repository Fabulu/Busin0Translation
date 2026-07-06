import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8')
# Check original extracted type-2 resources for FFD0-FFD9 usage vs FFFE.
# Find original packdata resources dir
cands = glob.glob(r"C:/programmieren/wizardrytranslation/data/**/packdata_resources/*", recursive=True)
cands += glob.glob(r"C:/programmieren/wizardrytranslation/extracted/**/R1197*", recursive=True)
cands += glob.glob(r"C:/programmieren/wizardrytranslation/**/1197*", recursive=True)
print("candidate R1197/type2 files:")
for c in cands[:20]:
    print("  ", c, os.path.getsize(c) if os.path.isfile(c) else "(dir)")
