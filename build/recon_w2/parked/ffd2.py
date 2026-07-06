import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
# v96 RAM resource
ee=open(r"C:/programmieren/wizardrytranslation/build/recon_tri/extract/requestbroken__ee.bin","rb").read()
res=0x011C3D00
so=struct.unpack_from("<I",ee,res+0x18)[0]
ss=struct.unpack_from("<I",ee,res+0x14)[0]
print("v96 RAM R1197 sec2off=0x%X sec2sz=0x%X"%(so,ss))
sec2=ee[res+so:res+so+ss]
nw=len(sec2)//2
words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(nw)]
print("total words:",nw)
for marker,name in [(0xFFD2,"FFD2"),(0xFFFE,"FFFE"),(0xFFFF,"FFFF")]:
    print(f"  {name} count:", words.count(marker))
# which groups (by FFFF index) contain FFD2
grp=0; ffd2groups=[]
g=[]
for w in words:
    g.append(w)
    if w==0xFFFF:
        if 0xFFD2 in g: ffd2groups.append((grp,len(g)))
        grp+=1; g=[]
print("groups containing FFD2:", ffd2groups[:20], "...total",len(ffd2groups))
# compare v99
v99=open("C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw","rb").read()
so2=struct.unpack_from("<I",v99,0x18)[0]; ss2=struct.unpack_from("<I",v99,0x14)[0]
s2=v99[so2:so2+ss2]; w2=[struct.unpack_from(">H",s2,i*2)[0] for i in range(len(s2)//2)]
print("\nv99 FFD2 count:", w2.count(0xFFD2), " FFFE count:", w2.count(0xFFFE))
