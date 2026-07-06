import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8')
# Which type-02 resources near the tavern were patched in v99 build? Look at patched_type2 dir
patched=sorted(glob.glob("C:/programmieren/wizardrytranslation/build/patched_type2/*.raw"))
ids=sorted(int(os.path.basename(p).split('_')[0]) for p in patched)
tavern=[i for i in ids if 1190<=i<=1215]
print("patched type-02 resources in tavern range 1190-1215:", tavern)
