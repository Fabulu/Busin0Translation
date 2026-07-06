import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
GM=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
HEADER_SIZE=0x20
DLG_OPEN=59  # イ-glyph used as dialogue open
DLG_CLOSE=61 # ゴ-glyph used as dialogue close
def load_sec(d):
    s=struct.unpack_from('<I',d,0x14)[0]; o=struct.unpack_from('<I',d,0x18)[0]
    return bytes(d[HEADER_SIZE:o]), bytes(d[o:o+s])
def parse_groups(sec2):
    n=len(sec2)//2; words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    groups=[];start=0
    for i,w in enumerate(words):
        if w==0xFFFF: groups.append((start,i)); start=i+1
    return groups,words,start
def find_group(groups,w):
    for gi,(gs,ge) in enumerate(groups):
        if gs<=w<=ge: return gi
    return None

# BLOCK-level signal: a 0x04 block is DIALOGUE if its concatenated glyph stream
# (across its groups) contains DLG_CLOSE (ゴ=61) as a terminator and/or starts
# region with DLG_OPEN (イ=59) or has a name marker.
# Test: does "block contains DLG_CLOSE 61" partition FFD2-blocks (dialogue) from
# narration blocks?  Use the KNOWN narration block (R1196 567-578 pure prose).
def block_glyphs(words, groups, off, cnt):
    gi0=find_group(groups,off); 
    if gi0 is None: return [],[]
    gi1=find_group(groups,min(off+cnt-1,groups[-1][1])) or gi0
    gl=list(range(gi0,gi1+1))
    seg=[]
    for gi in gl:
        gs,ge=groups[gi]; seg+=list(words[gs:ge])
    return gl,seg

stats={'ffd2_block_has_close':0,'ffd2_block_no_close':0,
       'noffd2_block_has_close':0,'noffd2_block_no_close':0}
ffd2_noclose_ex=[]
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    d=open(f,'rb').read()
    try: sec1,sec2=load_sec(d)
    except: continue
    groups,words,trailing=parse_groups(sec2)
    if not groups: continue
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    for r in recs['display']:
        if r['cnt']==0: continue
        gl,seg=block_glyphs(words,groups,r['off'],r['cnt'])
        if not seg: continue
        has_ffd2=0xFFD2 in seg
        has_close=DLG_CLOSE in seg
        if has_ffd2 and has_close: stats['ffd2_block_has_close']+=1
        elif has_ffd2 and not has_close:
            stats['ffd2_block_no_close']+=1
            if len(ffd2_noclose_ex)<20: ffd2_noclose_ex.append((rid,gl))
        elif not has_ffd2 and has_close: stats['noffd2_block_has_close']+=1
        else: stats['noffd2_block_no_close']+=1
print("BLOCK-level: 'block glyph stream contains ゴ(glyph 61) = dialogue-close'")
print(f"  FFD2 block & has-close (dialogue, consistent): {stats['ffd2_block_has_close']}")
print(f"  FFD2 block & NO close (would be FP risk):       {stats['ffd2_block_no_close']}")
print(f"  no-FFD2 & has-close (dialogue that fit 4 lines):{stats['noffd2_block_has_close']}")
print(f"  no-FFD2 & no-close (narration prose):           {stats['noffd2_block_no_close']}")
print(f"  FFD2-but-no-close examples: {ffd2_noclose_ex}")
