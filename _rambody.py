import struct
ram=open('runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/untranslatedlibrary/eeMemory.bin','rb').read()
def pack(ids,o='>H'): return b''.join(struct.pack(o,g) for g in ids)
anchors={'akusesari':[193,200,206,203,232,93],'touhan':[212,269,93,218,238],
 'item_compendium':[193,59,211,225,1289,677],'item_compendium2':[193,194,211,225,1289,677],
 'char_directory':[319,412,314,677],'title':[231,194,256,231,232,93]}
for o,lbl in [('>H','BE'),('<H','LE')]:
    for n,ids in anchors.items():
        p=pack(ids,o); c=ram.count(p); i=ram.find(p)
        if c: print('%s %-16s count=%d first@0x%X'%(lbl,n,c,i))
