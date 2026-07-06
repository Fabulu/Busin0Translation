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
EXACT={346:14512,411:20432,442:21056}
for t in [346,411,442]:
    code_base = gstarts[t]+len(groups[t])*2+2  # current "after FFFF" base
    exact = EXACT[t]
    print(f"G{t}: gstarts={gstarts[t]} len={len(groups[t])}")
    print(f"   current-code base (after FFFF) = {code_base}")
    print(f"   EXACT pristine base            = {exact}")
    print(f"   delta (exact - code) = {exact-code_base}")
    print(f"   exact - gstarts = {exact-gstarts[t]}")
    print(f"   first nonzero data group start = G{t+1 if len(groups[t+1]) else '?'} start={gstarts[t+1]}, start-exact={gstarts[t+1]-exact}")
    # The first content group (separator) start relative to exact base:
    print(f"   gstarts[{t+1}]-exact={gstarts[t+1]-exact}  gstarts[{t+2}]-exact={gstarts[t+2]-exact}")
