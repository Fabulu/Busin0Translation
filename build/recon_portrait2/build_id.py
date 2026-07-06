import sys
sys.stdout.reconfigure(encoding='utf-8')
# distinctive English strings from translation (v84+). Search EE RAM.
needles=[b'select a class', b'Bonus', b'Personality', b'PLAGUE', b'BLAMED', b'enter your name',
         b'affects damage', b'choose your']
import glob,os
for p in sorted(glob.glob('build/recon_portrait2/extract/*__ee.bin')):
    d=open(p,'rb').read()
    hits=[n.decode() for n in needles if n in d]
    print(os.path.basename(p).replace('__ee.bin',''), '-> EN markers:', hits if hits else 'NONE')
