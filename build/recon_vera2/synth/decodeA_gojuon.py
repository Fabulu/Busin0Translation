import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ee=open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
gojuon="あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
# katakana share same block at base 193 too (renderer picks font row). We'll show gojuon hiragana reading.
def dec193(v):
    if 193<=v<193+len(gojuon): return gojuon[v-193]
    if 33<=v<=58: return chr(v-33+65)  # ASCII A-Z
    if 65<=v<=90: return chr(v-65+97)
    if v==93: return 'ー'  # but 93<193 so won't hit; 93 = gojuon? 93-? no
    return f'<{v}>'
print("Array A (active party) base-193 gojuon decode:")
for s in range(6):
    rs=0x55DD20+s*0x1F0
    hdr=struct.unpack_from('<H',ee,rs)[0]
    vals=[];o=rs+2
    while o<rs+0x40:
        w=struct.unpack_from('<H',ee,o)[0]
        if w==0xFFFF: break
        vals.append(w); o+=2
    print(f"A{s} hdr={hdr:#06x} vals={vals} -> {''.join(dec193(v) for v in vals)}")
# value 93 appears (Basco slot2=...,93). 93 with base 193? no. Let me check what 93 is: long vowel ー
# In base-193, ー would be 193+? . Actually 93 is BELOW 193 so it's a separate special: long-vowel mark.
