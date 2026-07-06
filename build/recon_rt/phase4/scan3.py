import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
inj=open('build/recon_rt/phase4/out/1197_type02.raw','rb').read()
s2sz=struct.unpack_from('<I',inj,0x14)[0]; s2o=struct.unpack_from('<I',inj,0x18)[0]
sec2=inj[s2o:s2o+s2sz]
# is the FULL injected sec2 present contiguously in RAM?
idx=ee.find(sec2[:512])
print('sec2 head (512B) at', hex(idx) if idx>=0 else 'NOT FOUND')
if idx>=0:
    # check how many bytes match contiguously
    m=0
    while m<len(sec2) and idx+m<len(ee) and ee[idx+m]==sec2[m]:
        m+=1
    print(f'contiguous match: {m}/{len(sec2)} bytes ({100*m/len(sec2):.1f}%)')

# Section 1 present?
sec1=inj[0x20:s2o]
i1=ee.find(sec1[:256])
print('sec1 head (256B) at', hex(i1) if i1>=0 else 'NOT FOUND')
if i1>=0:
    m=0
    while m<len(sec1) and i1+m<len(ee) and ee[i1+m]==sec1[m]:
        m+=1
    print(f'sec1 contiguous: {m}/{len(sec1)} bytes')
