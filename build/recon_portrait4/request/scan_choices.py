import sys, struct, glob
sys.stdout.reconfigure(encoding='utf-8')

def sec1_sec2(path):
    d=open(path,'rb').read()
    s1_off=0x20
    # header layout: per CLAUDE.md type-02 has sub-header; sec2 ptr at 0x18
    s2_off=struct.unpack_from('<I',d,0x18)[0]
    return d, s1_off, s2_off

def groups_from_sec2(d, s2_off):
    """Parse FFFF-delimited groups in section 2 (big-endian u16 stream)."""
    end=len(d)
    body=d[s2_off:end]
    # read as BE u16
    words=[struct.unpack_from('>H',body,i)[0] for i in range(0,len(body)-1,2)]
    # find offset table: first words are offsets? We'll just scan for FFC0-FFCF markers
    return words

for rid in (1196,1197):
    for tag,base in (('JP','extracted/packdata_raw'),('CUR','build/packdata_resources')):
        p=f'{base}/{rid}_type02.raw'
        d,s1,s2=sec1_sec2(p)
        body=d[s2:]
        words=[struct.unpack_from('>H',body,i)[0] for i in range(0,len(body)-1,2)]
        choice=[(i,w) for i,w in enumerate(words) if 0xFFC0<=w<=0xFFCF]
        # count distinct markers and group boundaries (FFFF)
        ff=[i for i,w in enumerate(words) if w==0xFFFF]
        print(f"R{rid} {tag}: sec2@0x{s2:X} len={len(body)} nwords={len(words)} nFFFF={len(ff)} nCHOICE={len(choice)}")
        if choice:
            print(f"   choice markers: {[(i,hex(w)) for i,w in choice][:40]}")
    print()
