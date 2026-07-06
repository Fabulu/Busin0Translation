import sys
sys.stdout.reconfigure(encoding='utf-8')
EE="../recon_tri/extract/veraisjapanese__ee.bin"
ram=open(EE,'rb').read()

# slot1 Vera katakana = [193,194,232,205] as u16 LE
def pat(ids): return b''.join((v&0xFF).to_bytes(1,'little')+((v>>8)&0xFF).to_bytes(1,'little') for v in ids)

targets={
 'slot1_vera':[193,194,232,205],
 'slot2':[254,205,202,93],
 'slot3':[196,254,238],
 'slot4':[220,232,93,245,193],
 'slot5':[254,233,211,233,205],
}
for name,ids in targets.items():
    p=pat(ids)
    locs=[]
    start=0
    while True:
        i=ram.find(p,start)
        if i<0: break
        locs.append(i)
        start=i+1
    print(f"{name} {ids}: {len(locs)} hits -> {[hex(x) for x in locs]}")
