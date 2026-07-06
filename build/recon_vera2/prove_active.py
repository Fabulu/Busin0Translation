import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()
pristine=open("../../extracted/packdata_raw/1892_type20.raw",'rb').read()

# Active party slots 1-5 names (slot0=BABA player)
active=[
 [193,194,232,205],   #slot1
 [254,205,202,93],    #slot2
 [196,254,238],       #slot3
 [220,232,93,245,193],#slot4
 [254,233,211,233,205],#slot5
]
REC_BASE,REC_STRIDE=0x140,0x130
def rec_name(data,i):
    rs=REC_BASE+i*REC_STRIDE
    o=rs+2;out=[]
    while True:
        v=struct.unpack_from('<H',data,o)[0]
        if v==0xFFFF:break
        out.append(v);o+=2
    return out

print("Match active-party names to R1892 records 0-4:")
for s,nm in enumerate(active,1):
    for i in range(25):
        if rec_name(pristine,i)==nm:
            print(f"  active slot{s} {nm} == R1892 rec{i} (file 0x{REC_BASE+i*REC_STRIDE:X})")
            break
    else:
        print(f"  active slot{s} {nm} -> NO R1892 record match")

# So records 0-4 ARE the starting party. Their kana:
# rec0=[193,194,232,205]. In RECORDS 6-19 codec, base-193 gives アイリス.
# But it's actually Vera. Compare: rec9 (recruit Vera)=[273,270,93,231]=ヴェーラ
print("\nRecord 0 (active Vera):", rec_name(pristine,0))
print("Record 9 (recruit Vera):", rec_name(pristine,9))
print("=> SAME character, DIFFERENT glyph encoding between record-ranges 0-4 vs 6-19")
