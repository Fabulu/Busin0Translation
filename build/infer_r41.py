import struct,json,sys,os
sys.stdout.reconfigure(encoding="utf-8")
B="C:/Programmieren/wizardrytranslation"
with open(f"{B}/data/msg_glyph_map.json","r",encoding="utf-8-sig") as f: gm=json.load(f)
with open(f"{B}/build/infer_r41_map.json","r",encoding="utf-8-sig") as f: im=json.load(f)
with open(f"{B}/extracted/packdata_resources/0041_type01.bin","rb") as f: data=f.read()
ff=None
for o in range(0,len(data)-1,2):
    if struct.unpack(">H",data[o:o+2])[0]==0xFFFF: ff=o; break
sd=data[ff:]; n=len(sd)//2; vs=list(struct.unpack(f">{n}H",sd[:n*2]))
ms=[]; c=[]
for v in vs:
    if v==0xFFFF:
        if c: ms.append(c)
        c=[]
    elif v==0xFFFE: c.append(("L",0))
    elif v>=0xFFC0: c.append(("C",v))
    else: c.append(("G",v))
if c: ms.append(c)
fm=dict(gm)
for k,v in im.items():
    if k not in fm: fm[k]=v["char"]
dms=[]
for i,m in enumerate(ms):
    d=[]; u=[]
    for t,v in m:
        if t=="L": d.append("\n")
        elif t=="C": d.append(f"[C:{v:04X}]")
        else:
            s=str(v)
            if s in fm: d.append(fm[s])
            else: d.append(f"[{v}]"); u.append(v)
    tx="".join(d)
    dms.append({"index":i,"text":tx,"unknowns":u if u else None})
out={"_metadata":{"resource":"0041_type01.bin","game":"Busin 0 (Wizardry Alternative Neo)","agent":"infer-r41","date":"2026-05-22","location":"Church of Salem","msgs":len(dms),"inferred":len(im)},"inferred_mappings":im,"decoded_messages":dms}
with open(f"{B}/data/inferred_r41.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
for x in dms:
    t=x["text"].replace("\n"," | ")
    print(f"MSG {x[chr(105)+chr(110)+chr(100)+chr(101)+chr(120)]}: {t}")
    if x["unknowns"]: print(f"  UNK: {x[chr(117)+chr(110)+chr(107)+chr(110)+chr(111)+chr(119)+chr(110)+chr(115)]}")
print("DONE")
