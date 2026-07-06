#!/usr/bin/env python3
"""Trace the exact instruction sequence of the barkeep scene (R1197) around the
known dialogue g4 and narration interludes g7/g13, to find the precise structural
marker that separates DIALOGUE 0x04 from NARRATION 0x04 in the same scene."""
import os, sys, struct, json
os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0,'tools')
from sec1_disasm import walk, extract_records, LENB
from patch_section1_offsets import parse_sec2_group_offsets

raw=open('extracted/packdata_raw/1197_type02.raw','rb').read()
sec2_off=struct.unpack_from('<I',raw,0x18)[0]
sec2_size=struct.unpack_from('<I',raw,0x14)[0]
sec1=raw[0x20:sec2_off]; sec2=raw[sec2_off:sec2_off+sec2_size]
groups,_=parse_sec2_group_offsets(sec2)
ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)

def group_of(off):
    for gi,(gs,ge) in enumerate(groups):
        if gs<=off<=ge: return gi
    return None

disp={d['pc']:d for d in recs['display']}
labels={L['pc']:L for L in recs['label']}
namerefs={n['pc']:n for n in recs['name_ref']}

order=sorted(instrs)
# find pc of the 0x04 covering g4, g7, g13; print the 12 instrs before each
def find_disp_for_group(gi):
    for d in recs['display']:
        if d['cnt']==0: continue
        end=d['off']+d['cnt']
        cov=[x for x,(gs,ge) in enumerate(groups) if not (ge<d['off'] or gs>=end)]
        if cov and cov[0]==gi: return d['pc']
    return None

for tgt,lab in [(4,'DIALOGUE'),(7,'NARR'),(13,'NARR')]:
    dpc=find_disp_for_group(tgt)
    print(f"\n===== g{tgt} ({lab}) disp@pc=0x{dpc:x} =====")
    i=order.index(dpc)
    for j in range(max(0,i-10), i+1):
        pc=order[j]; op=instrs[pc]
        extra=''
        if op==0x14:
            L=labels[pc]; extra=f"  -> label off={L['off']} cnt={L['cnt']} grp={group_of(L['off'])}"
        elif op in (0x0C,0x0D):
            n=namerefs[pc]; extra=f"  -> nameref param={n['param']} idx={n['idx']}"
        elif op==0x04:
            d=disp[pc]; extra=f"  -> DISPLAY off={d['off']} cnt={d['cnt']} grp={group_of(d['off'])}"
        print(f"   pc=0x{pc:04x} op=0x{op:02x} len={LENB[op]}{extra}")
