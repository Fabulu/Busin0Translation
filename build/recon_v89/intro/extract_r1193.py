import struct, os, sys, json, hashlib
sys.stdout.reconfigure(encoding='utf-8')

HEADER_SIZE=0x20

def get_packdata_lba(iso):
    iso.seek(16*2048); pvd=iso.read(2048)
    root_lba=struct.unpack_from('<I',pvd,158)[0]
    iso.seek(root_lba*2048); rd=iso.read(4096)
    pos=0
    while pos<len(rd):
        ln=rd[pos]
        if ln==0: break
        nl=rd[pos+32]; nm=rd[pos+33:pos+33+nl].decode('ascii','replace')
        if 'PACKDATA' in nm: return struct.unpack_from('<I',rd,pos+2)[0]
        pos+=ln
    return None

def get_r1193(iso_path):
    with open(iso_path,'rb') as iso:
        base=get_packdata_lba(iso)*2048
        iso.seek(base+1193*12)
        so,sc,tc=struct.unpack('<III',iso.read(12))
        iso.seek(base+so*2048)
        return iso.read(sc*2048)

table=json.load(open('data/english_glyph_table.json',encoding='utf-8'))
rev={}
for ch,g in table.items(): rev.setdefault(g,ch)
def dec(g): return rev.get(g, chr(g+0x20) if g<=94 else f'<{g:04X}>')

for v in ['v86','v88','v89']:
    data=get_r1193(f'build/BUSIN0_EN_{v}.iso')
    sec2_size=struct.unpack_from('<I',data,0x14)[0]
    sec2_off=struct.unpack_from('<I',data,0x18)[0]
    nwords=sec2_size//2
    words=struct.unpack_from('>%dH'%nwords,data,sec2_off)
    trailing_start=0
    for i,w in enumerate(words):
        if w==0xFFFF: trailing_start=i+1
    print(f'=== {v} R1193: sec2={sec2_size}B nwords={nwords} trailing_start={trailing_start} trailing_words={nwords-trailing_start} md5={hashlib.md5(data[:sec2_off+sec2_size]).hexdigest()[:10]} ===')
    # scan section 1 for 0x14 records in trailing region
    sec1=data[HEADER_SIZE:sec2_off]
    recs=[]
    for pc in range(0,len(sec1)-13):
        if struct.unpack_from('>H',sec1,pc)[0]!=0x0014: continue
        if struct.unpack_from('>H',sec1,pc+4)[0]!=0xFFFF: continue
        off=struct.unpack_from('>I',sec1,pc+6)[0]
        cnt=struct.unpack_from('>I',sec1,pc+10)[0]
        if off>=trailing_start and cnt>0 and off+cnt<=nwords:
            recs.append((off,cnt,struct.unpack_from('>H',sec1,pc+2)[0]))
    recs.sort()
    for off,cnt,idx in recs:
        gl=words[off:off+cnt]
        txt=''.join(dec(g) for g in gl)
        print(f'  idx={idx:2d} off={off:4d} cnt={cnt:2d} |{txt}|')
    print()
