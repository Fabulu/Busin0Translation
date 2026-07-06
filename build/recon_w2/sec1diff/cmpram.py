import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
ram_sec1=ee[base:base+47136]
v99=open('build/patched_type2/1197_type02.raw','rb').read()
s2off=struct.unpack_from("<I",v99,0x18)[0]
v99_sec1=v99[0x20:s2off]
pri=open('extracted/packdata_raw/1197_type02.raw','rb').read()
pri_sec1=pri[0x20:struct.unpack_from("<I",pri,0x18)[0]]
print("lens ram=%d v99=%d pri=%d"%(len(ram_sec1),len(v99_sec1),len(pri_sec1)))
def diffcount(a,b):
    n=min(len(a),len(b)); d=[i for i in range(n) if a[i]!=b[i]]; return len(d),d[:10]
print("ram vs v99 sec1 diffs:",diffcount(ram_sec1,v99_sec1))
print("ram vs pri sec1 diffs:",diffcount(ram_sec1,pri_sec1))
print("v99 vs pri sec1 diffs:",diffcount(v99_sec1,pri_sec1)[0])
