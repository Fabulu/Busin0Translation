import sys, struct, os, glob
sys.stdout.reconfigure(encoding='utf-8')
RAW='extracted/packdata_raw'
def groups_of(res):
    p=f'{RAW}/{res:04d}_type02.raw'
    if not os.path.isfile(p): return None
    raw=open(p,'rb').read()
    sec2_size=struct.unpack_from('<I',raw,0x14)[0]
    sec2_off=struct.unpack_from('<I',raw,0x18)[0]
    sec2=raw[sec2_off:sec2_off+sec2_size]
    n=len(sec2)//2
    words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    grps=[];start=0
    for i in range(n):
        if words[i]==0xFFFF:
            grps.append(words[start:i]);start=i+1
    return grps

for res in [1196,1197]:
    g=groups_of(res)
    if g is None: 
        print(f"R{res}: missing"); continue
    print(f"R{res}: {len(g)} groups")
    # For each group, split on 0xFFFE/0xFFD2 line breaks, count glyphs per line (glyph < 0xFB00 only, exclude control >=0xFF00 and name slices)
    maxline=0; allcounts=[]
    for gi,grp in enumerate(g):
        # count run lengths between control words >=0xFB00
        run=0
        for w in grp:
            if w>=0xFB00:
                if run>0: allcounts.append(run); maxline=max(maxline,run)
                run=0
            else:
                run+=1
        if run>0: allcounts.append(run); maxline=max(maxline,run)
    allcounts.sort()
    print(f"  max glyph-run between breaks={maxline}")
    # histogram of top
    import collections
    c=collections.Counter(allcounts)
    top=sorted(c.items())[-10:]
    print(f"  top run-lengths:{top}")
