import json, struct, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
os.chdir('C:/programmieren/wizardrytranslation')
ee = open('ramdumps/_stillt3_ex/eeMemory.bin','rb').read()
gmap = json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
def gch(g):
    if g==0xFFFF:return '[END]'
    if g==0xFFFE:return '[LB]'
    if g==0:return '_'
    if 1<=g<95:return chr(0x20+g)
    return gmap.get(str(g),f'<{g}>')

# Dump the composed buffer around 0xe39d68 widely
base=0xe39c00
words=struct.unpack_from('>256H',ee,base)
print(f'=== composed buffer dump from 0x{base:08x} (BE u16) ===')
line=''
for i,w in enumerate(words):
    line+=gch(w)+' '
    if (i+1)%24==0:
        print(f'  +{i-23:3d}: {line}')
        line=''
print('  tail:',line)
