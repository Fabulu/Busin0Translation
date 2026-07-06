import zipfile, glob, os
def rp(p): return zipfile.ZipFile(p).read('eeMemory.bin')[0x4B0DD0:0x4B0DD0+32]
vals={}
for p in glob.glob('ramdumps/*.p2s'):
    try: b=rp(p)
    except: continue
    vals.setdefault(b.hex(),[]).append(os.path.basename(p))
total=sum(len(v) for v in vals.values())
print("Distinct values at 0x4B0DD0 across",total,"p2s dumps:")
for h,names in sorted(vals.items(), key=lambda kv:-len(kv[1])):
    print("  count=%3d  %s  e.g.%s"%(len(names),h,names[:2]))
print("Gate-intact (off4=05000124 AND off8=03004110) anywhere?",
      any(h[8:16]=="05000124" and h[16:24]=="03004110" for h in vals))
