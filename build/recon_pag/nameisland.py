import sys,struct,json,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
import patch_section1_offsets as P
from sec1_disasm import extract_records
from spans import load, groups_in_span
P._load_tables()
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def name_islands(res):
    """Return set of group indices whose 0x14 prefix decodes to a KNOWN speaker name,
    and propagate 'dialogue' to all groups in the same 0x04 body span."""
    L=load(res)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    if not ok: return None
    recs=extract_records(sec1,instrs)
    # groups that have a 0x14 prefix forming a clean name at offset 0
    named=set()
    for r in recs['label']:
        gi=P._find_group(groups,r['off'])
        if gi is None: continue
        gs,ge=groups[gi]
        if r['off']!=gs: continue  # must be a prefix at group start
        sl=words[r['off']:r['off']+r['cnt']]
        nm=P._decode_jp(sl)
        if nm and (nm in P._NAME_LABELS):
            named.add(gi)
    # now propagate: a 0x04 body span whose FIRST group is named -> whole span dialogue
    dlg=set()
    for r in recs['display']:
        if r['cnt']==0: continue
        sg=groups_in_span(groups,r['off'],r['cnt'])
        if sg and sg[0] in named:
            dlg.update(sg)
    return named, dlg, ok

if __name__=='__main__':
    overflow=json.load(open('build/recon_pag/overflow_worklist.json',encoding='utf-8'))
    byres={}
    for o in overflow: byres.setdefault(o['resource'],[]).append(o)
    nm_dlg=0; total_t2=0; no_island=0
    for res,items in sorted(byres.items()):
        if not os.path.isfile(f'extracted/packdata_raw/{res:04d}_type02.raw'): continue
        r=name_islands(res)
        if not r: continue
        named,dlg,ok=r
        for it in items:
            total_t2+=1
            if it['message'] in dlg: nm_dlg+=1
            else: no_island+=1
    print("type-02 overflow blocks:",total_t2)
    print("  with name-island (named speaker) in span -> DIALOGUE:",nm_dlg)
    print("  no name-island:",no_island)
