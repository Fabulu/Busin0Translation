import sys, os, glob, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets, _bucket_labels, _clean_prefix_len
from _helpers import parse_type02

PATCHED = os.path.join(ROOT, 'build', 'patched_type2')
for path in sorted(glob.glob(os.path.join(PATCHED, '*.raw')))[:5]:
    data = open(path,'rb').read()
    try:
        p = parse_type02(data)
    except Exception as e:
        print(os.path.basename(path), "parse fail", e); continue
    sec1 = p['sec1']
    ok, instrs = walk(sec1)
    if not ok:
        print(os.path.basename(path), "walk FAIL"); continue
    recs = extract_records(sec1, instrs)
    # build sec2 bytes
    sec2 = struct.pack('>%dH'%len(p['words']), *p['words'])
    groups, trailing_start = parse_sec2_group_offsets(sec2)
    per_group, trailing = _bucket_labels(recs['label'], groups, trailing_start)
    name_islands = {}
    for gi, slices in per_group.items():
        plen = _clean_prefix_len(slices)
        if plen is not None and 0 < plen < (groups[gi][1]-groups[gi][0]):
            name_islands[gi] = plen
    print(os.path.basename(path), "groups=%d labels=%d name_islands=%d"%(len(groups), len(recs['label']), len(name_islands)), dict(list(name_islands.items())[:8]))
