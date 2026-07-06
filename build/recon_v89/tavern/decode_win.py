import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
sys.path.insert(0,'build/recon_v86/tavern-submenu')

# deswizzle window 1 of R2147 from v87 and v89, save PNG, and diff
def deswizzle_psmt4(data, w, h, bw_psmt4, dbw_ct32):
    # try import from strip_patcher
    pass

# Just compare the two windows byte-wise; both md5 identical already, so confirm window content
for tag in ['v87','v89']:
    d=open(f'build/recon_v89/tavern/R2147_{tag}.raw','rb').read()
    w1=d[0x560:0x560+32768]
    w2=d[0x12020:0x12020+32768]
    dl=d[0:0x560]  # display list + upload records
    import hashlib
    print(tag,'win1',hashlib.md5(w1).hexdigest(),'win2',hashlib.md5(w2).hexdigest(),'dl',hashlib.md5(dl).hexdigest())
    # count non-bg nibbles in win1 as a sanity that text exists
