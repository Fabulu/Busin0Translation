import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P
S.parse_sec2_group_offsets = P.parse_sec2_group_offsets
S._find_group = P._find_group

def analyze(path):
    data = open(path,'rb').read()
    try:
        ok, instrs, sec1, sec2_off = S.walk_resource(data)
    except Exception as e:
        return None
    sec2 = data[sec2_off:]
    groups, trailing = S.parse_sec2_group_offsets(sec2)
    recs = S.extract_records(sec1, instrs)
    # map each 0x14 NAME label to its group
    name_groups = set()  # group indices that contain a 0x14 name-island
    for r in recs['label']:
        gi = S._find_group(groups, r['off'])
        if gi is not None:
            name_groups.add(gi)
    # For each 0x04 DISPLAY_TEXT, compute group range [g_first..g_last]
    blocks = []
    for d in recs['display']:
        off, cnt = d['off'], d['cnt']
        if cnt == 0: 
            continue
        g_first = S._find_group(groups, off)
        g_last  = S._find_group(groups, off+cnt-1)
        blocks.append({'pc':d['pc'],'off':off,'cnt':cnt,
                       'g_first':g_first,'g_last':g_last})
    return {'ok':ok,'n_groups':len(groups),'groups':groups,
            'name_groups':name_groups,'blocks':blocks,'recs':recs}

if __name__=='__main__':
    for p in sys.argv[1:]:
        r=analyze(p)
        name=os.path.basename(p)
        if r is None:
            print(name,"PARSE FAIL"); continue
        print(f"=== {name} ok={r['ok']} groups={r['n_groups']} "
              f"display_blocks={len(r['blocks'])} name_labels={len(r['recs']['label'])} "
              f"name_groups={sorted(r['name_groups'])[:20]}")
        for b in r['blocks']:
            span = b['g_last']-b['g_first']+1 if (b['g_first'] is not None and b['g_last'] is not None) else '?'
            # does ANY group in block range have name-island?
            has=False; first_has=False
            if b['g_first'] is not None and b['g_last'] is not None:
                for gi in range(b['g_first'], b['g_last']+1):
                    if gi in r['name_groups']:
                        has=True
                        if gi==b['g_first']: first_has=True
            print(f"  0x04@{b['pc']:#x} off={b['off']} cnt={b['cnt']} "
                  f"g[{b['g_first']}..{b['g_last']}] span={span} "
                  f"blockHasName={has} firstHasName={first_has}")
