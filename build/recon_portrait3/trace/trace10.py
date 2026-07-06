import sys
sys.stdout.reconfigure(encoding='utf-8')
# Reproduce the break-type assignment from build_v9 lines 388-396 for each 4-line string
def breaks(parts):
    # parts = list of line segments (after wrap). returns break type before each part index>0
    res=[]; lc=0
    for pi,part in enumerate(parts):
        if pi>0:
            lc+=1
            if lc>=3: res.append('PB(0xFFD2)'); lc=0
            else: res.append('LB(0xFFFE)')
    return res
cases={
 'Shady(577)':['Hey friend, hehe','--','you know where','God hides,','right?'],
 'Overflow(569)':['No one was in','sight. Not a','sound, not even','the wind.'],
 'Man(575)':['A man','approached,','staggering on','his feet.'],
}
for n,p in cases.items():
    print(n,"lines=",len(p))
    bk=breaks(p)
    for i,part in enumerate(p):
        pre=('  ['+bk[i-1]+'] ') if i>0 else '  '
        print(pre+repr(part))
