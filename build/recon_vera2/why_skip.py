import sys,json,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE="../.."
glyph_table=json.load(open(f"{BASE}/data/english_glyph_table.json",encoding='utf-8'))
name_labels=json.load(open(f"{BASE}/data/name_labels.json",encoding='utf-8'))
party_doc=json.load(open(f"{BASE}/data/r2654_party_names.json",encoding='utf-8'))
allowed=set(party_doc['entries'].values())

pristine=open(f"{BASE}/extracted/packdata_raw/1892_type20.raw",'rb').read()
build=open(f"{BASE}/build/packdata_resources/1892_type20.raw",'rb').read()
print("PRISTINE == BUILD R1892?", pristine==build, "(diffs:",sum(1 for i in range(len(pristine)) if pristine[i]!=build[i]),")")

KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv_to_kana(nv):
    if 193<=nv<=193+44: return KATA[nv-193]
    return KATA_EXTRA.get(nv,'〓')

REC_BASE,REC_STRIDE=0x140,0x130
raw=pristine
n=(len(raw)-REC_BASE)//REC_STRIDE
print(f"\n{n} records. Decoding each name to kana (using patcher's nv_to_kana):")
for i in range(n):
    rs=REC_BASE+i*REC_STRIDE
    rid=struct.unpack_from('<H',raw,rs)[0]
    vals=[];o=rs+2
    while o<rs+REC_STRIDE:
        v=struct.unpack_from('<H',raw,o)[0]
        if v==0xFFFF:break
        vals.append(v);o+=2
    if rid==0 or not vals: continue
    kana=''.join(nv_to_kana(v) for v in vals)
    eng=name_labels.get(kana)
    inallow = eng in allowed if eng else False
    print(f"  rec{i:2d} id={rid:3d} vals={vals} kana={kana!r} -> eng={eng!r} allowed={inallow}")
print("\nname_labels has 'ヴェーラ'?:", 'ヴェーラ' in name_labels, "->", name_labels.get('ヴェーラ'))
print("allowed set:", allowed)
