#!/usr/bin/env python3
"""Decode pristine JP groups from extracted/packdata_raw/1197_type02.raw
and classify each group BOX vs NARRATION using the leak_detector engine
(which reads the injected build/packdata_resources copy for Section-1)."""
import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/programmieren/wizardrytranslation'
os.chdir(ROOT)
sys.path.insert(0, 'build/recon_v86/scenebug/leak_detector')
sys.path.insert(0, 'tools')
from detect import parse_groups, find_group

GLYPH_MAP = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

def load_raw(path):
    data = open(path,'rb').read()
    sec2_off = struct.unpack_from("<I", data, 0x18)[0]
    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec1 = data[0x20:sec2_off]
    sec2 = data[sec2_off:sec2_off+sec2_size]
    return sec1, sec2

def decode_group(sec2, gs, ge):
    """Decode words [gs, ge) (ge is the FFFF index, exclusive)."""
    out=[]
    for wi in range(gs, ge):
        g = struct.unpack_from(">H", sec2, wi*2)[0]
        if g == 0xFFFF:
            break
        if g >= 0xFB00:
            # control word
            out.append('<%04X>'%g)
            continue
        ch = GLYPH_MAP.get(str(g))
        out.append(ch if ch is not None else '[%d]'%g)
    return ''.join(out)

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--lo', type=int, default=900)
    ap.add_argument('--hi', type=int, default=940)
    ap.add_argument('--raw', default='extracted/packdata_raw/1197_type02.raw')
    a = ap.parse_args()
    sec1, sec2 = load_raw(a.raw)
    groups, trailing = parse_groups(sec2)
    print('raw=%s  num groups=%d'%(a.raw, len(groups)))
    for gi in range(a.lo, min(a.hi+1, len(groups))):
        gs, ge = groups[gi]
        txt = decode_group(sec2, gs, ge)
        print('g%d [w%d:%d] %s' % (gi, gs, ge, txt))
