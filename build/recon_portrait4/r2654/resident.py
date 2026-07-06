import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
ee=open(f'{BASE}/build/recon_portrait4/extract/request__ee.bin','rb').read()
r2654=open(f'{BASE}/build/packdata_resources/2654_type44.raw','rb').read()
prist=open(f'{BASE}/extracted/packdata_raw/2654_type44.raw','rb').read()
# romaji 'Vera' name-value run BE: 149,164,177,160
vera_romaji_be=struct.pack('>4H',149,164,177,160)
# Is patched R2654 sub7 resident? search the sub7 block signature in EE
# sub7 in build starts with count=0x002F? Actually count 47=0x2f. Let's grab 32 bytes of build sub7 and search.
sub7_off=0x8210
sig=r2654[sub7_off:sub7_off+24]
def find_all(buf,pat,lim=20):
    out=[];s=0
    while True:
        i=buf.find(pat,s)
        if i<0:break
        out.append(i);s=i+1
        if len(out)>lim:break
    return out
print('romaji Vera BE-run in EE:', ['0x%x'%h for h in find_all(ee,vera_romaji_be)])
print('build sub7 24-byte sig in EE:', ['0x%x'%h for h in find_all(ee,sig)])
# Is R2654 even loaded? search a distinctive sub0 chunk
sub0=prist[0x2c0:0x2c0+32]
print('R2654 sub0 sig (32B) in EE:', ['0x%x'%h for h in find_all(ee,sub0)])
# Search the pristine sub7 katakana run for Vera (BE) -> would be loaded if pristine R2654 resident
vera_kana_be=struct.pack('>4H',273,270,93,231)
print('pristine-Vera kana BE-run in EE:', ['0x%x'%h for h in find_all(ee,vera_kana_be)])
