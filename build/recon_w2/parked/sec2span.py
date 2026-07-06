import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(path):
    b=open(path,"rb").read()
    sec2off=struct.unpack_from("<I",b,0x18)[0]
    sec2sz=struct.unpack_from("<I",b,0x14)[0]
    sec2=b[sec2off:sec2off+sec2sz]
    return b,sec2off,sec2sz,sec2
iso=open(r"C:/programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso","rb").read()
sig=bytes.fromhex("000000001fb800002000000000000000010000005c0e010040b80000")
idx=iso.find(sig)
import io,tempfile,os
# write orig to temp
ot="C:/programmieren/wizardrytranslation/build/recon_w2/parked/orig1197.raw"
open(ot,"wb").write(iso[idx:idx+0x20000])
for name,path,cnt in [("ORIG",ot,0x17),("V99","C:/programmieren/wizardrytranslation/build/patched_type2/1197_type02.raw",0x2F)]:
    b,so,ss,sec2=load(path)
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(min(80,len(sec2)//2))]
    print(f"\n{name}: sec2off=0x{so:X} sec2sz=0x{ss:X}  DISPLAY off=0 cnt={cnt}")
    # the span [0, cnt) — does word[cnt-1]==FFFF?
    print("  word[cnt-1]=0x%04X (%s)"%(words[cnt-1], "FFFF-terminated OK" if words[cnt-1]==0xFFFF else "NOT FFFF!"))
    print("  words[0:%d]:"%(cnt+2), " ".join("%04X"%w for w in words[:cnt+2]))
