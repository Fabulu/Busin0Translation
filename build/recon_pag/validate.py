import sys, os, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_pag')
from final_classify import block_signals, classify_block

# LABELED VALIDATION SET (group-level), from EXE+JP recon:
# KNOWN NARRATION groups (must classify NARRATION):
NARR={ (1196,568),(1196,569),(1196,575),(1196,577),(1196,616),
       (1193,0),(1193,1) }
# KNOWN DIALOGUE groups (must classify DIALOGUE):
DIAL={ (1197,903),(1197,904),(1197,905),(1197,906),(1197,907) }

def gi_class(res):
    r=block_signals(res)
    if not r or r[0]=='walkfail': return None
    ok,g,w,bl=r
    m={}
    for b in bl:
        c=classify_block(res,b)
        for gi in b['gis']:
            m[gi]=c
    return m

print("=== VALIDATION: known NARRATION (must be NARRATION) ===")
fp=0
for (res,gi) in sorted(NARR):
    m=gi_class(res); 
    c=m.get(gi,'(untargeted)') if m else '(walkfail)'
    flag='' if c in('NARRATION','(untargeted)','(walkfail)') else '  <-- FALSE POSITIVE!'
    if 'FALSE' in flag: fp+=1
    print("  R%d g%d -> %s%s"%(res,gi,c,flag))
print("=== VALIDATION: known DIALOGUE (should be DIALOGUE) ===")
for (res,gi) in sorted(DIAL):
    m=gi_class(res); c=m.get(gi,'(untargeted)') if m else '(walkfail)'
    print("  R%d g%d -> %s"%(res,gi,c))
print()
print("NARRATION->DIALOGUE false positives on labeled set:",fp)
