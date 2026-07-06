import sys, struct, json, glob, os
sys.stdout.reconfigure(encoding='utf-8')

# Basco = バスコー. kana grid: バ=254, ス=?, コ=?, ー=93
# from EXTRA: バ=254(0xfe). ス: KATA index? ス is index 12 in アイウエオカキクケコサシス -> 193+12=205=0xcd. コ=index9=202=0xca. ー=93=0x5d
# So Basco BE u16 = 00fe 00cd 00ca 005d
needle_basco_be = bytes([0x00,0xfe,0x00,0xcd,0x00,0xca,0x00,0x5d])
needle_vera_be = bytes([0x01,0x11,0x01,0x0e,0x00,0x5d,0x00,0xe7])
# LE versions
needle_basco_le = bytes([0xfe,0x00,0xcd,0x00,0xca,0x00,0x5d,0x00])
needle_vera_le = bytes([0x11,0x01,0x0e,0x01,0x5d,0x00,0xe7,0x00])

# Scan all extracted packdata raw files
files = sorted(glob.glob('extracted/packdata_raw/*.raw'))
print(f'scanning {len(files)} pristine packdata resources...')
for f in files:
    d=open(f,'rb').read()
    hits=[]
    for nm,n in [('Basco_BE',needle_basco_be),('Vera_BE',needle_vera_be),('Basco_LE',needle_basco_le),('Vera_LE',needle_vera_le)]:
        i=d.find(n)
        if i>=0: hits.append(f'{nm}@0x{i:x}')
    if hits:
        print(f'  {os.path.basename(f)}: {hits}')

# Also scan EXE
exe=glob.glob('extracted/*.78')+glob.glob('extracted/SLPM*')+glob.glob('*.78')
print('\nEXE candidates:', exe)
for e in exe:
    if os.path.isfile(e):
        d=open(e,'rb').read()
        for nm,n in [('Basco_BE',needle_basco_be),('Vera_BE',needle_vera_be),('Basco_LE',needle_basco_le),('Vera_LE',needle_vera_le)]:
            i=d.find(n)
            if i>=0: print(f'  {e}: {nm}@0x{i:x}')
