import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
PR='C:/programmieren/wizardrytranslation/build/packdata_resources'
DUMPS={
 'PRESENT':   f'{E2}/Firstdialogue__ee.bin',
 'nshadyman': f'{E}/nshadymanand4linesinsteadof3__ee.bin',
 'nosister':  f'{E}/nosister__ee.bin',
 'ladyknight':f'{E}/ladyknightnoportrait__ee.bin',
}
def load(p): return open(p,'rb').read()
bufs={k:load(v) for k,v in DUMPS.items()}

# candidate scene resources: dialogue-bearing type02. Test which resource's Section-1 prologue
# (first 0x80 bytes) is resident in each EE dump. Build a signature from each type02 raw.
import glob
cands=[]
for f in sorted(glob.glob(f'{PR}/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    if rid<1190 or rid>1260: continue
    d=open(f,'rb').read()
    s2=struct.unpack_from('<I',d,0x18)[0]
    sig=d[0x20:0x20+48]  # sec1 prologue
    cands.append((rid,sig,len(d)))
print(f"{len(cands)} candidate resources R1190-R1260")
for k,buf in bufs.items():
    print(f"--- {k} ---")
    hits=[]
    for rid,sig,ln in cands:
        if len(sig)>=16:
            idx=buf.find(sig)
            if idx>=0: hits.append((rid,idx))
    for rid,idx in hits[:10]:
        print(f"    R{rid} sec1-prologue resident @0x{idx:08X}")
    if not hits: print("    (no R1190-1260 sec1 prologue resident)")
