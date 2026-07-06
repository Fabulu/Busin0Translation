import sys, json, glob
sys.stdout.reconfigure(encoding='utf-8')
all_trans={}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        for e in json.load(open(fn,encoding='utf-8')):
            all_trans.setdefault(e['resource'],{})[e['msg_index']]=e.get('english','')
    except: pass
# find the complained lines
needles=['Hey friend','God hides','looking for','everywhere for',"That's why",'break the spirit','peerless','staggering','No one was in sight']
for res in sorted(all_trans):
    for mi,t in all_trans[res].items():
        if not t: continue
        for nd in needles:
            if nd in t:
                print(f"R{res} g{mi}: {t[:90]!r}")
                break
