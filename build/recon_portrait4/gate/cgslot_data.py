import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
RAW='C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251=open(f'{RAW}/1251_type01.raw','rb').read()
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
DUMPS={
 'PRESENT':   f'{E2}/Firstdialogue__ee.bin',
 'nshadyman': f'{E}/nshadymanand4linesinsteadof3__ee.bin',
 'nosister':  f'{E}/nosister__ee.bin',
 'ladyknight':f'{E}/ladyknightnoportrait__ee.bin',
}
def load(p): return open(p,'rb').read()
bufs={k:load(v) for k,v in DUMPS.items()}
CGSLOT=0x509F80
# Search the R1251 portrait payload (skip leading zeros) in each EE dump
src=R1251[0xA1:0xA1+128*256*4]
# find a distinctive nonzero needle
off=0
while off<len(src) and src[off]==0: off+=1
needle=src[off:off+512]
print(f"R1251 portrait needle at payload off {off}, len 512")
for k,buf in bufs.items():
    ptr=struct.unpack_from('<I',buf,CGSLOT)[0]
    idx=buf.find(needle)
    print(f"  {k:11s}: cgslot=0x{ptr:08X}  R1251 portrait pixels resident @0x{idx:08X}" if idx>=0 else f"  {k:11s}: cgslot=0x{ptr:08X}  R1251 portrait NOT resident")
    # also dump data at cgslot ptr
    if 0<ptr<len(buf):
        print(f"       data@cgslot: {buf[ptr:ptr+48].hex()}")
