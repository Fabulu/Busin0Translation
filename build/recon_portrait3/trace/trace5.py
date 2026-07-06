import sys, struct, json, glob, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build')
import patch_section1_offsets as P
P._load_tables()
ENG_REV=P._ENG_REV
def show(w):
    o=[]
    for g in w:
        if g==0xFFFE: o.append('|LB|')
        elif g==0xFFD2: o.append('|PB|')
        elif g==0xFFFF: o.append('|FF|')
        elif g>=0xFB00: o.append('<%04X>'%g)
        elif str(g) in P._GLYPH_MAP: o.append(P._GLYPH_MAP[str(g)])
        elif g in ENG_REV: o.append(ENG_REV[g])
        else: o.append('?%d'%g)
    return ''.join(o)

# The shady man encoded English starts with glyphs for "Hey friend,..."
# search the EE-RAM for the byte pattern of the encoded group.
target=bytes.fromhex('00280045005900000046005200490045004E0044000C')  # "Hey friend,"
ee=open('build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__ee.bin','rb').read()
import re
idxs=[m.start() for m in re.finditer(re.escape(target),ee)]
print("EE-RAM occurrences of 'Hey friend,' encoded:",[hex(i) for i in idxs])
for i in idxs[:4]:
    # read forward until FFFF
    end=i
    while end<len(ee)-1 and struct.unpack_from('>H',ee,end)[0]!=0xFFFF:
        end+=2
    w=[struct.unpack_from('>H',ee,j)[0] for j in range(i,end,2)]
    print(f"\n@RAM {hex(i)} ({len(w)}w):",show(w))
    print("  hex:",' '.join('%04X'%x for x in w))
