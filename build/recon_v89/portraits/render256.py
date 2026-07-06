import sys, os
sys.path.insert(0,'build/recon_v86/gs-vram-atlas'); import gs_atlas as G
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import struct

def grab(ts,outpref):
    path=G.SNAPS+f'/Busin 0 - Wizardry Alternative Neo_SLPM-65378_{ts}.gs.zst'
    v,draws,transfers,frames=G.parse_dump(path)
    for i,t in enumerate(transfers):
        if t['dbp']==0x3000 and t['rrw']==256 and t['rrh']==64:
            d=bytes(t['data'])
            w,h=256,64
            if len(d)>=w*h*4:
                im=Image.frombytes('RGBA',(w,h),d[:w*h*4])
                im.save(f'build/recon_v89/portraits/{outpref}_256x64_t{i}.png')
                print(f'{ts} t{i}: saved 256x64')
            break
    # also the 128x256 portrait if present
    for i,t in enumerate(transfers):
        if t['dbp']==0x3000 and t['rrw']==64 and t['rrh']==544:
            d=bytes(t['data'])
            # reinterpret as 128x256
            if len(d)>=128*256*4:
                im=Image.frombytes('RGBA',(128,256),d[:128*256*4])
                im.save(f'build/recon_v89/portraits/{outpref}_portrait128x256_t{i}.png')
                print(f'{ts} t{i}: saved portrait 128x256')
            break

grab('20260613134123','shadyman_noport')
grab('20260613134356','barkeep_withport')
