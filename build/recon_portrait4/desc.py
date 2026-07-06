import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def rd(p): return open(p,'rb').read()
EXTRACT='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract/'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
dumps={
 'PRESENT':REF,
 'nshadyman':EXTRACT+'nshadymanand4linesinsteadof3__ee.bin',
 'nosister':EXTRACT+'nosister__ee.bin',
 'ladyknight':EXTRACT+'ladyknightnoportrait__ee.bin',
}
DBASE=0x55DD20; STRIDE=0x1E0
data={n:rd(p) for n,p in dumps.items()}
# descriptor index 0
for idx in [0]:
    base=DBASE+idx*STRIDE
    print(f"\n=== descriptor idx {idx} @ 0x{base:08X} (stride 0x{STRIDE:X}) ===")
    for n,d in data.items():
        chunk=d[base:base+0x60]
        print(f"  {n:10}: {chunk[:0x40].hex()}")
# diff present vs each absent across full descriptor
ref=data['PRESENT']
for n in ['nshadyman','nosister','ladyknight']:
    d=data[n]
    base=DBASE
    diffs=[off for off in range(STRIDE) if d[base+off]!=ref[base+off]]
    print(f"\n  diff PRESENT vs {n} in descriptor 0 ({STRIDE}B): {len(diffs)} bytes differ")
    if diffs:
        # group
        for off in diffs[:40]:
            print(f"    +0x{off:03X}: ref={ref[base+off]:02X} {n}={d[base+off]:02X}")
