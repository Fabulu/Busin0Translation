import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk

def sec1(path):
    d=open(path,'rb').read()
    s2=struct.unpack_from('<I',d,0x18)[0]
    return d[0x20:s2], d, s2

for rid in (1196,1197):
    js,jd,js2=sec1(f'extracted/packdata_raw/{rid}_type02.raw')
    cs,cd,cs2=sec1(f'build/packdata_resources/{rid}_type02.raw')
    print(f"=== R{rid} ===")
    print(f"  JP sec1 len={len(js)} (sec2@0x{js2:X})  CUR sec1 len={len(cs)} (sec2@0x{cs2:X})")
    jok,ji=walk(js); cok,ci=walk(cs)
    print(f"  JP walk ok={jok} ninstr={len(ji)} | CUR walk ok={cok} ninstr={len(ci)}")
    # Is sec1 byte-identical? (Section-1 should change only at sec2 offset operands)
    same = js==cs
    print(f"  sec1 byte-identical JP==CUR: {same}")
    if not same and len(js)==len(cs):
        diffs=[i for i in range(len(js)) if js[i]!=cs[i]]
        print(f"  sec1 differs at {len(diffs)} byte positions; first 20: {diffs[:20]}")
    elif not same:
        print(f"  sec1 LENGTH differs! JP={len(js)} CUR={len(cs)}")
    # opcode map divergence
    allpc=sorted(set(ji)|set(ci))
    div=[pc for pc in allpc if ji.get(pc)!=ci.get(pc)]
    print(f"  opcode-map divergences: {len(div)}; first: {[hex(x) for x in div[:10]]}")
