import sys, struct, rabbitizer
sys.stdout.reconfigure(encoding='utf-8')
exe=open('extracted/SLPM_653.78','rb').read()
BASE=0xFFF80
def f(va): return va-BASE
# scan func_303C60 until jr ra
va=0x303C60
jals=[]
end=va+0x4000
pc=va
seen_jr=0
out=[]
while pc<end:
    raw=struct.unpack_from('<I',exe,f(pc))[0]
    ins=rabbitizer.Instruction(raw); ins.vram=pc
    a=ins.disassemble()
    if 'jal ' in a:
        jals.append((pc,a.split('jal')[1].strip()))
    if raw==0x03E00008:  # jr ra
        out.append(pc)
        # function likely ends; but there may be multiple; stop at first jr ra after some size
        if pc>va+0x100:
            break
    pc+=4
print("func ends ~0x%X"%pc)
from collections import Counter
c=Counter(j[1] for j in jals)
print("jal targets in func_303C60:")
for tgt,n in c.most_common():
    print(f"  {tgt}  x{n}  first@0x{[j[0] for j in jals if j[1]==tgt][0]:X}")
