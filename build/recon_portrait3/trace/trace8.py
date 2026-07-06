import sys, struct, re
sys.stdout.reconfigure(encoding='utf-8')
# unique encoded shady-man group (52 words from RAM)
pat=bytes.fromhex('0028004500590000004600520049004500'.replace(' ',''))  # "Hey friend" prefix
isos=['build/BUSIN0_EN_v90.iso','build/BUSIN0_EN_v9.iso','build/BUSIN0_EN_v89.iso','build/BUSIN0_EN_v88.iso','build/BUSIN0_EN.iso']
import os
for iso in isos:
    if not os.path.exists(iso): continue
    data=open(iso,'rb').read()
    idxs=[m.start() for m in re.finditer(re.escape(pat),data)]
    print(iso,"-> 'Hey friend' encoded occurrences:",len(idxs),[hex(i) for i in idxs[:3]])
