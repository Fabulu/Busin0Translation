import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE='C:/programmieren/wizardrytranslation/extracted/SLPM_653.78'
data=open(EXE,'rb').read()
def f2v(off): return off-0x80+0x100000
# Find lui at, 0x54 / lui rX,0x54 followed by addiu with imm near 0x2748 or 0x2660
# We scan all instructions: lui rd, 0x0054 => upper, then look for matching addiu/sw/sh with low offset in range
import collections
# collect lui targets: addr -> (reg, hi)
lui={}
for off in range(0,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26
    if op==0x0F: # lui
        rt=(w>>16)&31; imm=w&0xffff
        lui[off]=(rt,imm)
# Now find references producing addresses 0x542660..0x542800 and 0x55DD20..0x55E800
def reg(n): return ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'][n]
targets_lo=0x542600; targets_hi=0x542900
targets2_lo=0x55DD00; targets2_hi=0x55EA00
hits=[]
for off in range(0,len(data)-4,4):
    w=struct.unpack_from('<I',data,off)[0]
    op=w>>26
    if op==0x0F:
        rt=(w>>16)&31; hi=(w&0xffff)<<16
        # look ahead a few instrs for addiu/sw/sh using rt as base
        for j in range(1,6):
            o2=off+j*4
            if o2+4>len(data): break
            w2=struct.unpack_from('<I',data,o2)[0]
            op2=w2>>26; rs2=(w2>>21)&31; rt2=(w2>>16)&31; imm2=w2&0xffff
            simm=imm2-0x10000 if imm2&0x8000 else imm2
            if rs2==rt:
                addr=hi+simm
                if (targets_lo<=addr<targets_hi) or (targets2_lo<=addr<targets2_hi):
                    mn={0x09:'addiu',0x29:'sh',0x2B:'sw',0x28:'sb',0x21:'lh',0x23:'lw',0x25:'lhu',0x24:'lbu'}.get(op2,f'op{op2:#x}')
                    hits.append((f2v(off),f2v(o2),mn,reg(rt2),addr))
for h in hits:
    print(f"  lui@0x{h[0]:08X} -> {h[2]:5} ${h[3]:4} ref=0x{h[4]:08X}  (ins@0x{h[1]:08X})")
print(f"total {len(hits)}")
