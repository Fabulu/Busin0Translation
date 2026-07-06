import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
# Extract R1197 from v98 and v99 ISOs by header signature
sig_prefix=bytes.fromhex("000000001fb8000020000000000000000100")
def find_r1197(iso_path):
    data=open(iso_path,"rb").read()
    # there may be multiple matches; R1197 header sec2sz at +0x14 varies. Find all.
    res=[]
    i=data.find(sig_prefix)
    while i!=-1:
        res.append(i); i=data.find(sig_prefix,i+1)
    return data,res
for ver in ["v98","v99"]:
    path=f"C:/programmieren/wizardrytranslation/build/BUSIN0_EN_{ver}.iso"
    data,hits=find_r1197(path)
    # pick the one whose sec1 byte at 0x5D0 region decodes as our resource: check 0x10EC opcode 0x04
    found=None
    for h in hits:
        s1=data[h+0x20:h+0x20+0x1FB8]
        if len(s1)<0x10F6: continue
        if s1[0x10EC]==0x00 and s1[0x10ED]==0x04:  # 0x04 DISPLAY at 0x10EC
            found=h; break
    if found is None:
        print(ver,"R1197 not uniquely found, hits:",len(hits)); continue
    b=data[found:found+0x20000]
    so=struct.unpack_from("<I",b,0x18)[0]; ss=struct.unpack_from("<I",b,0x14)[0]
    sec2=b[so:so+ss]; w=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(len(sec2)//2)]
    # group1
    grps=[]; g=[]
    for x in w:
        g.append(x)
        if x==0xFFFF: grps.append(g); g=[]
    ffd2=w.count(0xFFD2)
    print(f"{ver}: R1197@{found:#x} sec2sz=0x{ss:X} groups={len(grps)} FFD2={ffd2} group1_len={len(grps[1]) if len(grps)>1 else '?'} g1_FFD2={0xFFD2 in grps[1] if len(grps)>1 else '?'}")
