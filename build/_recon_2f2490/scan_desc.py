import zipfile,struct,sys
RD=r"C:\programmieren\wizardrytranslation\ramdumps"
def ee(n):
    z=zipfile.ZipFile(RD+"\\"+n)
    return z.read('eeMemory.bin')
for n in sys.argv[1:]:
    m=ee(n)
    hits=[]
    for a in range(0x100000,0x2000000,4):
        if a+0x40>len(m): break
        bw=struct.unpack_from('<H',m,a+0x1c)[0]
        if bw==313:
            bx=struct.unpack_from('<h',m,a+0x3c)[0]
            hits.append((a,bx))
            if len(hits)>=8: break
    print(n,'bw=313 objs:',[(hex(a),bx) for a,bx in hits])
