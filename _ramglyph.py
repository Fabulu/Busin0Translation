import struct
ram=open('runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/untranslatedlibrary/eeMemory.bin','rb').read()
seqs={
 'item_compendium':[193,59,211,225,1289,677],
 'char_directory':[319,412,314,677],
 'adventure_guide':[486,487,136,276,901,118],
 'book_list':[419,412,232,205,212],
}
for order,lbl in [('>H','BE'),('<H','LE')]:
    print('====',lbl,'====')
    for name,ids in seqs.items():
        p=b''.join(struct.pack(order,g) for g in ids)
        i=ram.find(p); c=ram.count(p)
        print('  %-18s count=%d %s'%(name,c,('@0x%X'%i if i>=0 else '')))
