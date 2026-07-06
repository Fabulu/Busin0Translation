#!/usr/bin/env python3
# INVESTIGATION ONLY -- quantify translated-but-not-shipping type-02 messages.
import struct, json, glob, os, sys
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0,'tools')

SKIP_STRUCTURAL_GROUPS={(1197,1)}  # mirror build_v9 line 495

def parse_groups(data):
    nw=len(data)//2
    words=[struct.unpack_from('>H',data,i*2)[0] for i in range(nw)]
    groups=[]; start=0
    for i in range(nw):
        if words[i]==0xFFFF:
            groups.append((start,i)); start=i+1
    trailing_start=start
    return words, groups, trailing_start

def sec2(raw):
    size=struct.unpack_from('<I',raw,0x14)[0]
    off=struct.unpack_from('<I',raw,0x18)[0]
    return off,size,raw[off:off+size]

# Load type-2 translations exactly like build_v9 Step 4
all_trans={}
PREFIX_SKIP=('[DATA]','[LAYOUT]','[BINARY]','[MAP]','[SYSTEM]','[GLYPH')
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        d=json.load(open(fn,encoding='utf-8'))
        for e in d:  # build_v9 wraps the WHOLE file loop in try/except: a KeyError aborts the file
            r=e['resource']; mi=e['msg_index']
            if (r,mi) in SKIP_STRUCTURAL_GROUPS: continue
            en=e.get('english','')
            if not en: continue
            if any(en.startswith(p) for p in PREFIX_SKIP): continue
            if en.startswith('[DEBUG]'): continue
            if any(ord(c)>127 for c in en): continue
            all_trans.setdefault(r,{})[mi]=en
    except Exception as ex:
        pass

manifest=json.load(open('extracted/packdata_resources/manifest.json',encoding='utf-8'))
type02=set()
for r in all_trans:
    if r<len(manifest) and not manifest[r].get('skipped') and manifest[r].get('type_code')==2:
        type02.add(r)
type02.discard(1193)

report=[]
grand_total=0
for r_id in sorted(type02):
    raw_path=f'extracted/packdata_raw/{r_id:04d}_type02.raw'
    if not os.path.isfile(raw_path):
        continue
    raw=open(raw_path,'rb').read()
    if len(raw)<0x20: continue
    o_off,o_size,o_s2=sec2(raw)
    o_words,o_groups,o_trail=parse_groups(o_s2)
    n_groups=len(o_groups)

    built_path=f'build/packdata_resources/{r_id:04d}_type02.raw'
    has_built=os.path.isfile(built_path)
    if has_built:
        braw=open(built_path,'rb').read()
        b_off,b_size,b_s2=sec2(braw)
        b_words,b_groups,b_trail=parse_groups(b_s2)
    else:
        # not patched at all -> ships pristine (original); every translated group is Japanese
        b_groups=None

    trans_idxs=sorted(all_trans[r_id].keys())
    # classify each translated msg_index
    still_jp=[]
    out_of_range=[]
    for mi in trans_idxs:
        if mi<0 or mi>=n_groups:
            out_of_range.append(mi)
            continue
        og=o_words[o_groups[mi][0]:o_groups[mi][1]]
        if not has_built or b_groups is None:
            still_jp.append(mi); continue
        if mi>=len(b_groups):
            still_jp.append(mi); continue
        bg=b_words[b_groups[mi][0]:b_groups[mi][1]]
        if list(bg)==list(og):
            # group content byte-identical to original JP => NOT translated/shipped
            still_jp.append(mi)
    affected=len(still_jp)+len(out_of_range)
    if affected>0:
        report.append((r_id,affected,len(still_jp),len(out_of_range),n_groups,has_built,still_jp,out_of_range))
        grand_total+=affected

print("RESID  affected  identical-to-JP  out-of-range  ngroups  built")
for r_id,aff,sj,oo,ng,hb,sjl,ool in report:
    print(f"R{r_id:<5} {aff:>5}     {sj:>5}          {oo:>5}      {ng:>5}    {hb}")
print()
print("GRAND TOTAL translated-but-Japanese messages:", grand_total)
print("Affected resources:", len(report))
# Save detail
json.dump([{'res':r,'affected':a,'identical_jp':s,'out_of_range':o,'ngroups':n,'built':hb,
            'still_jp_idx':sj,'oor_idx':oo} for (r,a,s,o,n,hb,sj,oo) in report],
          open('build/_scope_quantify_detail.json','w'),indent=1)
