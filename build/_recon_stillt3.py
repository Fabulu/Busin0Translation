import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
BASE='C:/programmieren/wizardrytranslation'
os.chdir(BASE)

ee = open('ramdumps/_stillt3_ex/eeMemory.bin','rb').read()
r39_built = open('build/packdata_resources/0039_type15.raw','rb').read()
r39_orig  = open('extracted/packdata_raw/0039_type15.raw','rb').read()

R39_EE = 0xe33900   # base in EE
print('R39 EE base', hex(R39_EE))

# Pull the live R39 region from eeMemory (same length as built)
live = ee[R39_EE:R39_EE+len(r39_built)]

print('live==built?', live==r39_built)
print('live==orig (32768 padded)?', live[:len(r39_orig)]==r39_orig)

# diff count between live and built
diffs = [i for i in range(min(len(live),len(r39_built))) if live[i]!=r39_built[i]]
print('num byte diffs live vs built:', len(diffs))
if diffs:
    print('first diffs:', [(hex(d), live[d], r39_built[d]) for d in diffs[:10]])

# scan FFFF groups in BUILT file from 632
def scan(raw):
    pos=632; groups=[]; starts=[]; cur=[]; cs=pos
    while pos+1<len(raw):
        w=struct.unpack_from('>H',raw,pos)[0]
        if w==0xFFFF:
            groups.append(cur); starts.append(cs); cur=[]; cs=pos+2
        else:
            cur.append(w)
        pos+=2
    return groups,starts

g,s = scan(r39_built)
print('built groups', len(g))
print('G442 start', s[442], 'len', len(g[442]))
print('G442 raw slots:', g[442][:20])
print('G442 slot8 =', g[442][8])

# slot8==340 check (v115 signature)
print('IS_V115 (G442 slot8==340):', g[442][8]==340)
