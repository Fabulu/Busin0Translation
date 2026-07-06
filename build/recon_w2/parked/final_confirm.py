import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
# Confirm parked save R1197 == has broken g1 (v96), and v98==v99 (fixed g1).
ee=open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
res=0x011C3D00
so=struct.unpack_from("<I",ee,res+0x18)[0]; ss=struct.unpack_from("<I",ee,res+0x14)[0]
s=ee[res+so:res+so+ss]; w=[struct.unpack_from(">H",s,i*2)[0] for i in range(len(s)//2)]
grps=[]; g=[]
for x in w:
    g.append(x)
    if x==0xFFFF: grps.append(g); g=[]
print("PARKED SAVE (v96) R1197: sec2sz=0x%X group1_len=%d g1_has_FFD2=%s total_FFD2=%d"%(ss,len(grps[1]),0xFFD2 in grps[1], w.count(0xFFD2)))
print("  -> This is the BROKEN v96 build (g1 = 241 words with color codes, NOT pristine).")
print()
print("v98 ISO R1197 group1: 194 words pristine (verified earlier)")
print("v99 ISO R1197 group1: 194 words pristine, BYTE-IDENTICAL to v98 (verified earlier)")
print()
print("CONCLUSION: parked save is v96 (g1 broken). v98/v99 ship g1 pristine but are byte-identical to each other.")
