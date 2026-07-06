import struct, json, os, sys
os.chdir('C:/programmieren/wizardrytranslation')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
raw = open('extracted/packdata_raw/0039_type15.raw','rb').read()
pos=632; groups=[]; gstarts=[]; cur=[]; cs=pos
while pos+1<len(raw):
    w=struct.unpack_from('>H',raw,pos)[0]
    if w==0xFFFF: groups.append(cur); gstarts.append(cs); cur=[]; cs=pos+2
    else: cur.append(w)
    pos+=2
allstarts=set(gstarts)
start_to_gi={gstarts[i]:i for i in range(len(gstarts))}

# For each table, find base where each DISTINCT nonzero offset maps to a unique group START,
# and the sequence of groups is strictly increasing.
tables={346:(347,380),381:(383,411),411:(412,442),442:(443,477)}
for t,(glo,ghi) in tables.items():
    vals=groups[t]
    offs=[vals[i*2] for i in range(len(vals)//2)]
    nz_unique=sorted(set(o for o in offs if o!=0))
    best=None
    for B in range(gstarts[t], gstarts[t]+300):
        tgs=[B+o for o in nz_unique]
        if all(x in allstarts for x in tgs):
            gis=[start_to_gi[x] for x in tgs]
            if gis==sorted(gis) and len(set(gis))==len(gis):
                best=(B,gis); break
    if best:
        B,gis=best
        print(f"G{t}: EXACT base={B} (= gstarts[{t}]+{B-gstarts[t]}); {len(nz_unique)} unique offsets -> groups G{gis[0]}..G{gis[-1]}")
    else:
        # relax: count max starts
        bb=None
        for B in range(gstarts[t]-20,gstarts[t]+300):
            h=sum(1 for o in nz_unique if (B+o) in allstarts)
            if bb is None or h>bb[1]: bb=(B,h)
        print(f"G{t}: no perfect base. best={bb[0]} hits={bb[1]}/{len(nz_unique)}")
