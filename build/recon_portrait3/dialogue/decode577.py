import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
JP='C:/programmieren/wizardrytranslation/extracted/packdata_raw/1196_type02.raw'
CUR='C:/programmieren/wizardrytranslation/build/packdata_resources/1196_type02.raw'
def sec2_groups(path):
    d=open(path,'rb').read()
    s2off=struct.unpack_from('<I',d,0x18)[0]
    sec2=d[s2off:]
    words=[struct.unpack_from('>H',sec2,i)[0] for i in range(0,len(sec2)-1,2)]
    groups=[]; cur=[]
    for w in words:
        if w==0xFFFF:
            groups.append(cur); cur=[]
        else:
            cur.append(w)
    return groups,s2off
jg,jo=sec2_groups(JP); cg,co=sec2_groups(CUR)
print(f"JP sec2_off=0x{jo:X} ngroups={len(jg)} | CUR sec2_off=0x{co:X} ngroups={len(cg)}")
def classify(w):
    if w==0xFFFE: return 'LF'
    if w==0xFFD2: return 'PGBRK'
    if 0xFFF0<=w<=0xFFF6: return f'VAR{w&0xF}'
    if 0xFFC0<=w<=0xFFCF: return f'CHOICE{w&0xF}'
    if w>=0xFB00: return f'CTL{w:04X}'
    return None
def dump(g,idx,tag):
    out=[]
    for w in g:
        c=classify(w)
        out.append(f'<{c}>' if c else f'{w:04x}')
    print(f"  [{tag} g{idx}] n={len(g)}: "+' '.join(out))
for i in range(574,582):
    if i<len(cg): dump(cg[i],i,'CUR')
print()
for i in range(574,582):
    if i<len(jg): dump(jg[i],i,'JP')
