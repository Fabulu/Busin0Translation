import sys, struct, glob, os
sys.stdout.reconfigure(encoding='utf-8')
RAW='C:/programmieren/wizardrytranslation/extracted/packdata_raw'
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
lk=open(f'{E}/ladyknightnoportrait__ee.bin','rb').read()
# Which type01 CG resources (portrait-ish) are resident in the tavern dump?
# Portraits are likely R1250-R1260 range type01. Probe each.
for f in sorted(glob.glob(f'{RAW}/*_type01.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    if rid<1240 or rid>1280: continue
    d=open(f,'rb').read()
    # distinctive needle skipping leading zeros from payload at 0xA1
    pl=d[0xA1:0xA1+0x8000]
    off=0
    while off<len(pl) and pl[off]==0: off+=1
    if off+256>len(pl): continue
    needle=pl[off:off+256]
    idx=lk.find(needle)
    if idx>=0:
        print(f"  R{rid} type01 resident in ladyknight EE @0x{idx:08X}")
