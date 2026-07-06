import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
# EE .bin = full 32MB, vaddr0 = fileoff0
def rd(path):
    return open(path,'rb').read()
def u16(d,va): return struct.unpack_from('<H',d,va)[0]
def s16(d,va): 
    v=struct.unpack_from('<H',d,va)[0]; return v-0x10000 if v&0x8000 else v
def u32(d,va): return struct.unpack_from('<I',d,va)[0]
EXTRACT='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract/'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
dumps={
 'PRESENT(Firstdialogue)':REF,
 'absent(nshadyman)':EXTRACT+'nshadymanand4linesinsteadof3__ee.bin',
 'absent(nosister)':EXTRACT+'nosister__ee.bin',
 'absent(ladyknight)':EXTRACT+'ladyknightnoportrait__ee.bin',
 'guy(Ithink)':EXTRACT+'Ithinkguyshouldshowuphere__ee.bin',
 'request':EXTRACT+'request__ee.bin',
}
SLOT=0x542748
for name,p in dumps.items():
    try: d=rd(p)
    except Exception as e:
        print(name,'ERR',e); continue
    if len(d)<0x600000:
        print(name,'short',len(d)); continue
    slots=[s16(d,SLOT+i*2) for i in range(6)]
    # slot id array region around 0x542734 flags
    flags=[d[0x542734+i] for i in range(14)]
    print(f"\n== {name} len={len(d)//(1024*1024)}MB ==")
    print(f"  slot table 0x542748 (6): {slots}")
    print(f"  flag bytes 0x542734..: {flags}")
