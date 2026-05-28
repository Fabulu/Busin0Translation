import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
O = r'C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\recon44-kanji-ram'
with open(os.path.join(O, 'eeMemory.bin'), 'rb') as f:
    ram = f.read()
hh = []
for i in range(0, len(ram)-10, 2):
    if ram[i+1]==0x82 and 0xA0<=ram[i]<=0xF1:
        c = 1
        j = i+2
        while j+1<len(ram) and ram[j+1]==0x82 and 0xA0<=ram[j]<=0xF1:
            c += 1
            j += 2
        if c >= 5:
            hh.append((i, c))
print('Hiragana 5+: %d' % len(hh))
for a,c in hh[:20]:
    cs=[]
    for k in range(c):
        try: cs.append(bytes([ram[a+k*2+1],ram[a+k*2]]).decode('shift_jis'))
        except: cs.append('?')
    print('  0x%08X: %d %s' % (a, c, ''.join(cs)))
kh = []
for i in range(0, len(ram)-10, 2):
    if ram[i+1]==0x83 and 0x40<=ram[i]<=0x96:
        c = 1
        j = i+2
        while j+1<len(ram) and ram[j+1]==0x83 and 0x40<=ram[j]<=0x96:
            c += 1
            j += 2
        if c >= 5:
            kh.append((i, c))
print('Katakana 5+: %d' % len(kh))
for a,c in kh[:20]:
    cs=[]
    for k in range(c):
        try: cs.append(bytes([ram[a+k*2+1],ram[a+k*2]]).decode('shift_jis'))
        except: cs.append('?')
    print('  0x%08X: %d %s' % (a, c, ''.join(cs)))
print('Done.')
