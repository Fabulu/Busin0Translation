import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets

def load(path):
    raw=open(path,'rb').read()
    s2o=struct.unpack_from('<I',raw,0x18)[0]; s2sz=struct.unpack_from('<I',raw,0x14)[0]
    sec1=raw[0x20:s2o]; sec2=raw[s2o:s2o+s2sz]
    return sec1,sec2

for tag,path in [('PRISTINE','extracted/packdata_raw/1197_type02.raw'),
                 ('INJECTED','build/recon_rt/phase4/out/1197_type02.raw')]:
    sec1,sec2=load(path)
    ok,instrs=walk(sec1)
    groups,trailing=parse_sec2_group_offsets(sec2)
    recs=extract_records(sec1,instrs)
    # validate every display off lands on a group start; cnt within range
    bad=0
    gstarts={gs for gs,ge in groups}
    for D in recs['display']:
        off,cnt=D['off'],D['cnt']
        if off not in gstarts: bad+=1
    print(f'{tag}: walk_ok={ok} instrs={len(instrs)} groups={len(groups)} display={len(recs["display"])} label={len(recs["label"])} display_off_not_group_start={bad}')
