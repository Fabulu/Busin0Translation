import sys
sys.stdout.reconfigure(encoding='utf-8')
ee = open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
res=0x011C3D00
ram = ee[res:res+0x1FB8+0x20]
patched = open("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw","rb").read()
backup  = open("C:/programmieren/wizardrytranslation/build/packdata_resources_backup/1197_type02.raw","rb").read()
# Section1 = bytes [0x20 .. 0x20+0x1FB8)
s_ram = ram[0x20:0x20+0x1FB8]
s_v99 = patched[0x20:0x20+0x1FB8]
s_pre = backup[0x20:0x20+0x1FB8]
def cmp(a,b,na,nb):
    diffs=[i for i in range(min(len(a),len(b))) if a[i]!=b[i]]
    print(f"{na} vs {nb}: {len(diffs)} differing bytes" + (f", first@{diffs[0]:#x}" if diffs else ""))
    return diffs
d1=cmp(s_ram,s_v99,"RAM(v96)","patched(v99)")
d2=cmp(s_ram,s_pre,"RAM(v96)","backup(pre/pristine)")
d3=cmp(s_v99,s_pre,"patched(v99)","backup(pre)")
# show first few diffs
for d,a,b in [(d1,s_ram,s_v99)]:
    for i in d[:20]:
        print("  off %05X: ram=%02x v99=%02x"%(i,a[i],b[i]))
