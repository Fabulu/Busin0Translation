import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
ram_hex="0028 0045 0059 0000 0046 0052 0049 0045 004E 0044 000C 0000 0048 0045 0048 0045 FFFE 000D 000D FFFE 0059 004F 0055 0000 004B 004E 004F 0057 0000 0057 0048 0045 0052 0045 FFD2 0027 004F 0044 0000 0048 0049 0044 0045 0053 000C FFFE 0052 0049 0047 0048 0054 001F".split()
ram=bytes.fromhex(''.join(ram_hex))
for iso,off in [('build/BUSIN0_EN_v90.iso',0x1b0ebd98),('build/BUSIN0_EN_v9.iso',0x1b0ebd98)]:
    data=open(iso,'rb').read()
    chunk=data[off:off+len(ram)]
    print(iso,"match RAM group:",chunk==ram)
# Also check v89 full group to see if word-wrap was present pre-regression
data=open('build/BUSIN0_EN_v89.iso','rb').read()
off=0x1b0ebdae
chunk=data[off:off+len(ram)]
print("v89 group == RAM:",chunk==ram, "| v89 hex:",' '.join('%02X'%b for b in chunk[:54]))
