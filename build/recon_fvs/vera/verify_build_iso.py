import sys,struct,os
sys.stdout.reconfigure(encoding='utf-8')
def le(words): return b''.join(struct.pack('<H',w) for w in words)
vera_le=le([273,270,93,231]); vera_ascii_le=le([149,164,177,160])
# Is R1892 patched in build/packdata_resources?
for f in ['extracted/packdata_raw/1892_type20.raw','build/packdata_resources/1892_type20.raw']:
    if os.path.exists(f):
        b=open(f,'rb').read()
        print('%s: vera_le@%s vera_ascii@%s'%(f, '0x%X'%b.find(vera_le) if vera_le in b else 'NONE', '0x%X'%b.find(vera_ascii_le) if vera_ascii_le in b else 'NONE'))
    else:
        print(f,'MISSING')
# check the v92 ISO for both R1892 katakana and R2654 ascii
iso='build/BUSIN0_EN_v92.iso'
if os.path.exists(iso):
    print('ISO size',os.path.getsize(iso))
    # search ISO directly
    data=open(iso,'rb').read()
    print('ISO vera_le (R1892 katakana present):', '0x%X'%data.find(vera_le) if vera_le in data else 'NONE')
    print('ISO vera_ascii_le:', '0x%X'%data.find(vera_ascii_le) if vera_ascii_le in data else 'NONE')
    # R2654 ascii BE Vera 149,164,177,160 BE
    vera_ascii_be=b''.join(struct.pack('>H',w) for w in [149,164,177,160])
    print('ISO vera_ascii_BE (R2654 patch present):', '0x%X'%data.find(vera_ascii_be) if vera_ascii_be in data else 'NONE')
else:
    print('ISO MISSING')
