import sys,struct,os,glob
sys.stdout.reconfigure(encoding='utf-8')
def le(words): return b''.join(struct.pack('<H',w) for w in words)
def be(words): return b''.join(struct.pack('>H',w) for w in words)
vera_le=le([273,270,93,231]); vera_be=be([273,270,93,231])
# Aurora full roster sig as LE and BE
aur_le=le([193,195,235,93,231]); aur_be=be([193,195,235,93,231])
# also the LE roster: stride-0x1F0 means name at struct+0; search any resource for vera LE
d='extracted/packdata_raw'
hits=[]
for f in sorted(glob.glob(d+'/*.raw')):
    b=open(f,'rb').read()
    r={}
    for nm,pat in [('vera_le',vera_le),('vera_be',vera_be),('aur_le',aur_le),('aur_be',aur_be)]:
        if pat in b: r[nm]=b.find(pat)
    if r: hits.append((os.path.basename(f),len(b),r))
for h in hits: print(h)
print('total resources scanned:',len(glob.glob(d+'/*.raw')))
