import struct
ram=open('runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/untranslatedlibrary/eeMemory.bin','rb').read()
seqs={'item_compendium':[193,59,211,225,1289,677],'char_directory':[319,412,314,677]}
# search for each individual glyph id, find positions, then look for stride patterns
def find_all(b, sub):
    out=[]; i=ram.find(sub)
    while i>=0 and len(out)<40:
        out.append(i); i=ram.find(sub,i+1)
    return out
for order,lbl in [('>H','BE'),('<H','LE')]:
    for name,ids in seqs.items():
        first=struct.pack(order,ids[0]); second=struct.pack(order,ids[1])
        pos=find_all(ram,first)
        for p in pos:
            # try strides 2..8 to find second id
            for stride in (2,3,4,6,8):
                if ram[p+stride:p+stride+2]==second:
                    print('%s %s firstid@0x%X stride=%d'%(lbl,name,p,stride))
                    break
