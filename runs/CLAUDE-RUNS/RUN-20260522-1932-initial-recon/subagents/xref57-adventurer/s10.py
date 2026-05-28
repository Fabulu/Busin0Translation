import struct,os,json
R=r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
H=r'C:/Programmieren/wizardrytranslation/dumps/msg_header_analysis.json'
hdr=json.load(open(H))
gs_map={r['index']:r.get('glyph_start_offset',0) for r in hdr['resources']}
idx=45
fp=next(os.path.join(R,fn) for fn in os.listdir(R) if fn.startswith('0045_') and fn.endswith('.bin'))
data=open(fp,'rb').read()
gs=gs_map[idx]
region=data[gs:]
n=len(region)//2
vals=list(struct.unpack('>%dH'%n,region))
msgs,cur=[],[]
for v in vals:
    if v==0xFFFF:
        if cur: msgs.append(cur)
        cur=[]
    else: cur.append(v)
if cur: msgs.append(cur)
for mi in [7,11,22]:
    msg=msgs[mi]
    hx=' '.join('%04X'%v for v in msg)
    print('msg#%d full: %s'%(mi,hx))
    lines,cl=[],[]
    for v in msg:
        if v==0xFFFE: lines.append(cl);cl=[]
        else: cl.append(v)
    lines.append(cl)
    for i,l in enumerate(lines):
        print('  line%d (%d): %s'%(i,len(l),' '.join('%04X'%v for v in l)))
    print()