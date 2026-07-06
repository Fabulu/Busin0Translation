import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
BASE="C:/programmieren/wizardrytranslation"
pris=open(BASE+"/extracted/packdata_raw/1892_type20.raw",'rb').read()
gt=json.load(open(BASE+"/data/english_glyph_table.json",encoding='utf-8'))
REC_BASE=0x140; REC_STRIDE=0x130; NAME_OFF=2
def raw_glyph(ch):
    if ch in gt: return gt[ch]
    if ch.lower() in gt: return gt[ch.lower()]
    return 31
# field span for a record (bytes from name to after FFFF, incl FF pad)
def span(raw,noff):
    o=noff
    while struct.unpack_from('<H',raw,o)[0]!=0xFFFF: o+=2
    end=o+2
    while end<noff+REC_STRIDE-2 and raw[end]==0xFF: end+=1
    return end-noff
names={9:'Vera',10:'Erika',11:'Konde',6:'Frieder',7:'Melanie',13:'Turgot',
       0:'Iris',1:'Basco',2:'Evan',3:'Freesia',4:'Baltels',12:'Iris',14:'Aoi',18:'Uli',19:'Melanie'}
print("RAW-GLYPH (correct) encoding per record:")
for rec,eng in sorted(names.items()):
    noff=REC_BASE+rec*REC_STRIDE+NAME_OFF
    sp=span(pris,noff)
    need=(len(eng)+1)*2
    enc=b''.join(struct.pack('<H',raw_glyph(c)) for c in eng)+struct.pack('<H',0xFFFF)
    vals=[raw_glyph(c) for c in eng]
    fits = need<=sp
    print(f"  rec{rec:2d} {eng:<8s} raw-glyph={vals} bytes={enc.hex()} need={need} field={sp} {'FIT' if fits else 'OVERFLOW'}")
# Specifically Vera:
noff=REC_BASE+9*REC_STRIDE+NAME_OFF
print(f"\nVera @file 0x{noff:X}: current pristine = {pris[noff:noff+10].hex()}")
print(f"  -> patch to RAW-glyph: {b''.join(struct.pack('<H',raw_glyph(c)) for c in 'Vera').hex()}ffff")
print(f"  raw glyphs V,e,r,a = {[raw_glyph(c) for c in 'Vera']}  (all <95 => R2100 ASCII cells)")
