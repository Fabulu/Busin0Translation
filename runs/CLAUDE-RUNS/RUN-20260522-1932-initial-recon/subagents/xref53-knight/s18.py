import struct,os
RD=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
def frf(i):
    for fn in os.listdir(RD):
        if fn.startswith(str(i).zfill(4)+'_'):return os.path.join(RD,fn)
    return None
tgts=[34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,896,1084,1092,1134,1144,1161,1285,1288,1289,1909,2106,2108,2115,2478,2654,2791,2797,2821,2856]
found=0
for idx in tgts:
    p=frf(idx)
    if not p:continue
    with open(p,'rb') as f:d=f.read()
    i=0
    while i<len(d)-1:
        v=struct.unpack('>H',d[i:i+2])[0]
        if v==0xFFFF:
            g=[];j=i+2
            while j<len(d)-1:
                w=struct.unpack('>H',d[j:j+2])[0]
                if w==0xFFFF:break
                if w!=0xFFFE:g.append(w)
                j+=2
            if 35<=len(g)<=42 and g and all(x<=1100 for x in g):
                if g[1]==g[8]:
                    found+=1
                    if found<=20:print('R%d len=%d v=%d %s'%(idx,len(g),g[1],str(g[:12])+'...'))
            i=j
        else:i+=2
print('Total p1=p8 matches: '+str(found))
