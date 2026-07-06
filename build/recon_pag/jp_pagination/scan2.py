import sys, os, struct, glob, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records

HEADER_SIZE = 0x20
RAW_DIR = 'build/packdata_resources'

def res_id(path): return int(os.path.basename(path).split('_')[0])
def load_sec(data):
    s=struct.unpack_from('<I',data,0x14)[0]; o=struct.unpack_from('<I',data,0x18)[0]
    return bytes(data[HEADER_SIZE:o]), bytes(data[o:o+s])
def parse_groups(sec2):
    n=len(sec2)//2; words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    groups=[]; start=0
    for i,w in enumerate(words):
        if w==0xFFFF: groups.append((start,i)); start=i+1
    return groups, words, start
def find_group(groups, woff):
    for gi,(gs,ge) in enumerate(groups):
        if gs<=woff<=ge: return gi
    return None

# For the critical name=N ffd2=Y blocks, examine the WINDOW of groups around them:
# does any nearby group (within +-2) carry a 0x14 name-island? This tests whether
# dialogue blocks have a name-island in a SEPARATE 0x04, distinguishing them from
# pure narration (which never has a name-island anywhere in the surrounding block).

targets = {
 1196:[(19,22),(116,117),(531,532),(719,722)],   # narration (intro)
 1197:[(904,912)],                                # Barkeep dialogue (g905)
}

def analyze(rid, gl):
    f=f'build/packdata_resources/{rid:04d}_type02.raw'
    data=open(f,'rb').read(); sec1,sec2=load_sec(data)
    groups,words,trailing=parse_groups(sec2)
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    nameisland=set()
    label_off_by_group={}
    for r in recs['label']:
        gi=find_group(groups,r['off'])
        if gi is not None:
            nameisland.add(gi)
            label_off_by_group.setdefault(gi,[]).append((r['off']-groups[gi][0], r['cnt']))
    # name_ref (0x0C/0x0D) groups - these SET a speaker name slot
    g0=gl[0]; g1=gl[-1]
    win=range(max(0,g0-3), min(len(groups), g1+4))
    print(f"  R{rid} block groups {g0}..{g1}:")
    for gi in win:
        gs,ge=groups[gi]; seg=words[gs:ge]
        flags=[]
        if 0xFFD2 in seg: flags.append('FFD2')
        if 0xFFFE in seg: flags.append('FFFE')
        if gi in nameisland: flags.append(f'NAME-ISLAND{label_off_by_group[gi]}')
        mark='>>' if g0<=gi<=g1 else '  '
        # decode first ~16 glyphs as hex
        head=' '.join(f'{w:04X}' for w in seg[:10])
        print(f"   {mark} g{gi} len={ge-gs} [{','.join(flags) or '-'}] {head}")
    print()

for rid,blks in targets.items():
    print(f"=== R{rid} ===")
    for (a,b) in blks:
        analyze(rid, list(range(a,b+1)))
