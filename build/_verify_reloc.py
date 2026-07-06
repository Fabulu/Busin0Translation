"""Verify relocated files in v139 ISO match the original extracted files byte-for-byte."""
import struct, hashlib, os

orig = r'C:\programmieren\wizardrytranslation\Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
v139 = r'C:\programmieren\wizardrytranslation\build\BUSIN0_EN_v139.iso'
SECTOR = 2048

def dir_map(path):
    with open(path,'rb') as f:
        f.seek(16*SECTOR); pvd=f.read(SECTOR)
        rl=struct.unpack_from('<I',pvd,158)[0]; rs=struct.unpack_from('<I',pvd,166)[0]
        f.seek(rl*SECTOR); dd=f.read(rs)
    out={}; pos=0
    while pos<len(dd):
        r=dd[pos]
        if r==0: break
        nl=dd[pos+32]; nm=dd[pos+33:pos+33+nl].decode('ascii','replace').split(';')[0]
        lba=struct.unpack_from('<I',dd,pos+2)[0]; sz=struct.unpack_from('<I',dd,pos+10)[0]
        if nm not in ('\x00','\x01'): out[nm]=(lba,sz)
        pos+=r
    return out

def md5_region(path, lba, size):
    h=hashlib.md5()
    with open(path,'rb') as f:
        f.seek(lba*SECTOR)
        remaining=size
        while remaining>0:
            chunk=f.read(min(1<<20, remaining))
            if not chunk: break
            h.update(chunk); remaining-=len(chunk)
    return h.hexdigest()

def md5_file(path):
    h=hashlib.md5()
    with open(path,'rb') as f:
        while True:
            c=f.read(1<<20)
            if not c: break
            h.update(c)
    return h.hexdigest()

do=dir_map(orig); dv=dir_map(v139)
print(f"{'FILE':16s} {'orig_LBA':>9s} {'v139_LBA':>9s} {'size':>11s}  result")
ext=r'C:\programmieren\wizardrytranslation\extracted'
extmap={
 'BSN2_0.DSI':'BSN2_0.DSI','PADMAN.IRX':'PADMAN.IRX','SIO2MAN.IRX':'SIO2MAN.IRX',
 'MCSERV.IRX':'MCSERV.IRX','MODMIDI.IRX':'MODMIDI.IRX','MUS.IRX':'MUS.IRX',
 'LIBSD.IRX':'LIBSD.IRX','MODMSIN.IRX':'MODMSIN.IRX','MODHSYN.IRX':'MODHSYN.IRX',
 'MCMAN.IRX':'MCMAN.IRX','IOPRP254.IMG':'IOPRP254.IMG','SYSTEM.CNF':'SYSTEM.CNF',
}
for nm in do:
    if nm=='PACKDATA.DIG' or nm not in dv: continue
    ol,os_=do[nm]; vl,vs=dv[nm]
    # compare v139 region vs orig region (both by their own dir entries)
    om=md5_region(orig, ol, os_)
    vm=md5_region(v139, vl, vs)
    res='IDENTICAL' if om==vm else '*** DIFFERS ***'
    # also compare vs extracted file when available
    note=''
    efn=extmap.get(nm)
    if efn:
        ep=os.path.join(ext,efn)
        if os.path.exists(ep):
            em=md5_file(ep)
            if em==vm: note=' (==extracted)'
            elif em==om: note=' (orig==extracted, v139 DIFFERS)'
            else: note=' (neither matches extracted!)'
    print(f"{nm:16s} {ol:>9d} {vl:>9d} {os_:>11d}  {res}{note}")
