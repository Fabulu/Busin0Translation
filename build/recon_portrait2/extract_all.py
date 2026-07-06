import zipfile, zstandard, struct, sys, os
sys.path.insert(0,'build/recon_portrait2')
sys.stdout.reconfigure(encoding='utf-8')
from extract_one import raw_member_bytes

OUT='build/recon_portrait2/extract'
os.makedirs(OUT,exist_ok=True)
FILES=['knighterguy.p2s','knightguy.ps2.p2s','Firstdialogue.p2s','randomdialogue.p2s',
       'taverndialoguev3.p2s','moreenglish.p2s','Blackscreenafterintro2twocharactersentered.p2s',
       'ingamev3one.p2s','ingamev3two.p2s']

def write_member(path, name, out):
    raw,fsize,ctype=raw_member_bytes(path,name)
    if raw[:4]==b'\x28\xb5\x2f\xfd':
        data=zstandard.ZstdDecompressor().stream_reader(raw).read()
    else:
        data=zipfile.ZipFile(path).read(name)
    open(out,'wb').write(data); return len(data)

for f in FILES:
    base=f.replace('.p2s','').replace('.ps2','')
    p='RAMdumps/'+f
    which=sys.argv[1] if len(sys.argv)>1 else 'shot'
    if which=='shot':
        n=write_member(p,'Screenshot.png',f'{OUT}/{base}__shot.png'); print(f'{base} screenshot {n}')
    elif which=='gs':
        n=write_member(p,'GS.bin',f'{OUT}/{base}__gs.bin'); print(f'{base} gs {n}')
    elif which=='ee':
        n=write_member(p,'eeMemory.bin',f'{OUT}/{base}__ee.bin'); print(f'{base} ee {n}')
