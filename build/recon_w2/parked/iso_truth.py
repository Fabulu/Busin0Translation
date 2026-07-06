import sys, glob, struct, os
sys.stdout.reconfigure(encoding='utf-8')
# Find the ORIGINAL untouched ISO and its PACKDATA. Look for original ISO.
isos=glob.glob("C:/programmieren/wizardrytranslation/**/*.iso", recursive=True)
print("ISOs:")
for i in isos:
    print("  ", i.replace("C:/programmieren/wizardrytranslation/",""), os.path.getsize(i))
# Also look for an original PACKDATA.DIG
digs=glob.glob("C:/programmieren/wizardrytranslation/**/PACKDATA*", recursive=True)
print("PACKDATA files:")
for d in digs:
    print("  ", d.replace("C:/programmieren/wizardrytranslation/",""), os.path.getsize(d) if os.path.isfile(d) else "DIR")
