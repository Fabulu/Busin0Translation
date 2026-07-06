import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
# Check R1251 BITBLT presence in the GS dump for the missing-portrait scene
gs=open('build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__gs.bin','rb').read()
print("GS size",len(gs))
# VRAM at data_start+425 per CLAUDE.md GS tooling note
# Check CG slot ptr in EE RAM BSS 0x509F80 (vaddr) -> file off = vaddr (eeMemory vaddr0=fileoff0)
ee=open('build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__ee.bin','rb').read()
for nm,va in [('cgslot 0x509F80',0x509F80),('chanbit0 0x565110',0x565110),('chanbit1 0x5650D0',0x5650D0),('chanbit2 0x565090',0x565090)]:
    val=struct.unpack_from('<I',ee,va)[0]
    print(f"{nm} = {val:08X}")
