import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
# decode the specific .word move/or instrs in 2F3700 handler manually
words={
0x2f3704:0xffbf0030,0x2f3708:0x7fb20020,0x2f3710:0x0080902d,0x2f371c:0x0040882d,
0x2f3724:0x0240202d,0x2f3728:0x0040802d,0x2f3738:0x0240202d,0x2f373c:0x0220282d,
0x2f3740:0x0200302d,0x2f3774:0x0240202d,0x2f3794:0x0240202d,0x2f3798:0x0220282d,
0x2f379c:0x0200302d,0x2f37a4:0x0000382d,0x2f37b0:0x0240202d,0x2f37b4:0x0220282d,
0x2f37b8:0x0200302d,0x2f37c0:0x0000382d,
}
R=['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','s8','ra']
for a in sorted(words):
    w=words[a]; op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; fn=w&0x3f; sh=(w>>6)&31
    if op==0 and fn==0x25: # or
        print("0x%08x: or       $%s,$%s,$%s"%(a,R[rd],R[rs],R[rt]))
    elif op==0 and fn==0x2d: # daddu (move on this)
        print("0x%08x: move     $%s,$%s  (daddu)"%(a,R[rd],R[rs]))
    elif op==0 and fn==0x21: # addu
        print("0x%08x: addu     $%s,$%s,$%s"%(a,R[rd],R[rs],R[rt]))
    else:
        print("0x%08x: %08x op=%x fn=%x rs=%s rt=%s rd=%s"%(a,w,op,fn,R[rs],R[rt],R[rd]))
