import sys
sys.stdout.reconfigure(encoding='utf-8')
ee = open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__ee.bin","rb").read()
base=0x55DD20
stride=0x1F0
for s in range(6):
    off=base+s*stride+2
    glyphs=[]
    p=off
    while True:
        v=ee[p] | (ee[p+1]<<8)
        if v==0xFFFF: break
        glyphs.append(v)
        p+=2
        if len(glyphs)>16: break
    print(f"slot{s} @0x{off:X} = {glyphs}")
