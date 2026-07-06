import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
# Minimal MIPS LE assembler for the caves we need.
REG={n:i for i,n in enumerate(["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7","s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","s8","ra"])}
def R(n): return n if isinstance(n,int) else REG[n]
def I(op,rs,rt,imm): return ((op&0x3f)<<26)|((R(rs)&0x1f)<<21)|((R(rt)&0x1f)<<16)|(imm&0xffff)
def Rt(rs,rt,rd,sa,f): return ((R(rs)&0x1f)<<21)|((R(rt)&0x1f)<<16)|((R(rd)&0x1f)<<11)|((sa&0x1f)<<6)|(f&0x3f)
def J(op,tgt): return ((op&0x3f)<<26)|((tgt>>2)&0x03FFFFFF)
def addiu(rt,rs,i): return I(9,rs,rt,i)
def addu(rd,rs,rt): return Rt(rs,rt,rd,0,0x21)
def subu(rd,rs,rt): return Rt(rs,rt,rd,0,0x23)
def lh(rt,off,rs): return I(0x21,rs,rt,off)
def lhu(rt,off,rs): return I(0x25,rs,rt,off)
def lbu(rt,off,rs): return I(0x24,rs,rt,off)
def sh(rt,off,rs): return I(0x29,rs,rt,off)
def lui(rt,i): return I(0x0f,0,rt,i)
def ori(rt,rs,i): return I(0x0d,rs,rt,i)
def andi(rt,rs,i): return I(0x0c,rs,rt,i)
def beq(rs,rt,tgt,pc): return I(4,rs,rt,(tgt-(pc+4))>>2)
def bne(rs,rt,tgt,pc): return I(5,rs,rt,(tgt-(pc+4))>>2)
def j(tgt): return J(2,tgt)
def nop(): return 0
def disp(words,base):
    sys.path.insert(0,'build'); from _r7_dis import dec
    for i,w in enumerate(words):
        va=base+i*4; print(f'  {va:08X}: {w:08X}  {dec(w,va)}')

# ============ NARRATION SUM-CENTERING CAVE ============
# Cave NS at VA 0x4B0E00. Two entry points: NS_A (for 0x3c, reserve 224) and NS_B (0x3e, 192).
# Both walk s5+0x40 (lh, stride2, -1 term) summing ADV[g]; reserve = BASE - SUM.
# Registers free to clobber at the centering site: a0,v1 (and we use t0,t1,t2,t3 as scratch).
# We must NOT clobber a1 (count, used later) -> actually after the centering block a1 is
# dead? Check: at 0x3059A0 the next block reloads everything (a1=-1 etc). Safe to clobber a1.
# ADV table: reuse Patch14's table @ VA 0x4C7564 (adv_table_256). base reg lui 0x4C ori 0x7564.
NS = 0x4B0E00
ADV_TBL = 0x4C7564   # = Patch14 P14_TBL1 (adv_table_256)
def sum_center(base_reg_va, reserve_base, store_off, ret_va, pc0):
    # in: s5=desc ptr. out: sh (reserve_base - SUM) to store_off(s5); j ret_va
    # t0 = &glyph array = s5+0x40 ; t1 = SUM ; t2 = glyph ; t3 = ADV base ; v1 = adv
    w=[]
    pc=pc0
    w.append(addiu("t0","s5",0x40)); pc+=4          # t0 = glyph array
    w.append(addiu("t1","zero",0)); pc+=4           # t1 = SUM = 0
    w.append(lui("t3",(ADV_TBL>>16)&0xffff)); pc+=4
    w.append(ori("t3","t3",ADV_TBL&0xffff)); pc+=4  # t3 = ADV table base
    loop=pc
    w.append(lh("t2",0,"t0")); pc+=4                # t2 = glyph (signed)
    # if t2 == -1 -> done
    done_placeholder=len(w)
    w.append(0); pc+=4   # beq t2,?,-1 ... fill later
    w.append(nop()); pc+=4
    w.append(andi("t2","t2",0xff)); pc+=4           # gid
    w.append(addu("at","t3","t2")); pc+=4           # &ADV[gid]
    w.append(lbu("v1",0,"at")); pc+=4               # adv
    w.append(addu("t1","t1","v1")); pc+=4           # SUM += adv
    w.append(addiu("t0","t0",2)); pc+=4             # next glyph
    w.append(j(loop)); pc+=4
    w.append(nop()); pc+=4
    done=pc
    # fill the beq -1
    # need register holding -1; use 'at'? at not set. Use slti? Simpler: compare via addiu at,zero,-1 earlier.
    # Re-do: we need -1 compare. Insert 'at=-1' before loop. Let's restructure.
    return None
# The -1 compare needs an immediate. Restructure cleanly below.
def sum_center2(reserve_base, store_off, ret_va, pc0):
    w=[]; pc=pc0
    def emit(x):
        nonlocal pc; w.append(x); pc+=4
    emit(addiu("t0","s5",0x40))       # t0 = glyph array ptr
    emit(addiu("t1","zero",0))        # SUM=0
    emit(addiu("t9","zero",-1))       # t9 = -1 terminator
    emit(lui("t3",(ADV_TBL>>16)&0xffff))
    emit(ori("t3","t3",ADV_TBL&0xffff))
    loop=pc
    emit(lh("t2",0,"t0"))             # glyph (signed)
    beq_pc=pc; beq_idx=len(w); emit(0)           # beq t2,t9,done (fill)
    emit(nop())
    emit(andi("v1","t2",0xff))        # gid
    emit(addu("at","t3","v1"))
    emit(lbu("v1",0,"at"))            # adv
    emit(addu("t1","t1","v1"))
    emit(addiu("t0","t0",2))
    emit(j(loop)); emit(nop())
    done=pc
    w[beq_idx]=beq("t2","t9",done,beq_pc)
    # v1 = reserve_base - SUM ; sh v1,store_off(s5)
    emit(addiu("v1","zero",reserve_base))
    emit(subu("v1","v1","t1"))
    emit(sh("v1",store_off,"s5"))
    emit(j(ret_va)); emit(nop())
    return w,pc

# Block A (0x3c, base 224, return 0x3059A0)
nsA,after_a=sum_center2(224,0x3c,0x3059A0,NS)
print("=== NARRATION SUM-CENTER A @0x%X (224 - SUM -> 0x3c) ret 0x3059A0 ==="%NS)
disp(nsA,NS)
NS_B=after_a
nsB,after_b=sum_center2(192,0x3e,0x305A10,NS_B)
print("\n=== NARRATION SUM-CENTER B @0x%X (192 - SUM -> 0x3e) ret 0x305A10 ==="%NS_B)
disp(nsB,NS_B)
print("\nNarration caves end at VA 0x%X"%after_b)
print("HOOK A: at 0x305988 -> j 0x%X (delay nop); replaces sll/addu/sll/subu/sh (0x305988..0x305998)"%NS)
print("HOOK B: at 0x3059F8 -> j 0x%X (delay nop); replaces 0x3059F8..0x305A08"%NS_B)

print("\n\n############ CHARGEN PATH 1 CAVES ############")
# ---- Chargen ADV cave: hook 0x308040 (addiu v0,v0,0x18). Replace with j cave.
#   At 0x308040: v0 = pen (lh'd at 0x30803C from 0x1cc(sp)). s1 = glyph array ptr
#   (NOT yet +2). gid = lh(0x40(s1)) & 0xff. v0 += ADV[gid]; sh v0,0x1cc(sp); ret 0x308048.
#   Free regs: v0(pen),v1,at,t-regs. s-regs MUST be preserved (s0=idx,s1=ptr,s2,s3,s5,s6,s7,s4).
#   Use v1,at,t8 as scratch (t8 not used by loop body around here).
CG = after_b  # = 0x4B0EA0
def chargen_adv(pc0):
    w=[];pc=pc0
    def emit(x):
        nonlocal pc; w.append(x); pc+=4
    emit(lh("v1",0x40,"s1"))          # v1 = glyph (re-read; s1 not bumped yet)
    emit(andi("v1","v1",0xff))        # gid
    emit(lui("at",(ADV_TBL>>16)&0xffff))
    emit(ori("at","at",ADV_TBL&0xffff))
    emit(addu("at","at","v1"))
    emit(lbu("v1",0,"at"))            # adv
    emit(addu("v0","v0","v1"))        # pen += adv   (v0 holds pen, lh'd at 0x30803C)
    emit(j(0x308048)); emit(nop())    # return past the sh? -- NO, sh is at 0x308044
    return w,pc
# WAIT: 0x308044 is `sh v0,0x1cc(sp)`. We must keep storing. Cave does sh then ret 0x308048.
def chargen_adv2(pc0):
    w=[];pc=pc0
    def emit(x):
        nonlocal pc; w.append(x); pc+=4
    emit(lh("v1",0x40,"s1"))
    emit(andi("v1","v1",0xff))
    emit(lui("at",(ADV_TBL>>16)&0xffff))
    emit(ori("at","at",ADV_TBL&0xffff))
    emit(addu("at","at","v1"))
    emit(lbu("v1",0,"at"))
    emit(addu("v0","v0","v1"))
    emit(sh("v0",0x1cc,"sp"))         # store pen (replaces 0x308044)
    emit(j(0x308048)); emit(nop())    # return to loop tail
    return w,pc
cga,cga_end=chargen_adv2(CG)
print("=== CHARGEN ADVANCE LUT @0x%X ; hook 0x308040 -> j; replaces 0x308040+0x308044 ==="%CG)
disp(cga,CG)

# ---- Chargen DRAW-SHIFT (Stage 2, Option A): subtract LEFTSHIFT[g] from penX in
#   0x1cc(sp) immediately before jal 0x305E30 @ 0x308030. We hook 0x308030 (the jal)
#   -> j cave; cave reloads penX, subtracts LEFTSHIFT[gid], stores BACK to 0x1cc(sp),
#   re-does the jal's setup (the delay slot 0x308034 `addu t0,v1,v0` uses v1=penX,v0=draw)
#   ... PROBLEM: penX is passed to 0x305E30 via 0x1cc(sp) read at 0x308018 (v1) BEFORE
#   the jal. So shifting 0x1cc(sp) before 0x308018 is needed, OR shift v1 directly.
#   Cleaner: hook 0x308018 (lh v1,0x1cc(sp)) -> after load, subtract LEFTSHIFT from v1.
#   But v1 is also stored? No. v1 = penX used at 0x308034 addu t0,v1,v0. So adjust v1.
LSH_TBL = 0x4C7690  # = Patch14 P14_TBL2 (leftshift_table_256)
def chargen_shift(pc0):
    # hook at 0x308018 `lh v1,0x1cc(sp)`. cave: v1=penX; gid=lh(0x40(s1))&0xff;
    #   v1 -= LSH[gid]; (clamp >=0 optional); j 0x30801C. scratch: at,t8 (a0..a3 set later).
    w=[];pc=pc0
    def emit(x):
        nonlocal pc; w.append(x); pc+=4
    emit(lh("v1",0x1cc,"sp"))         # displaced original
    emit(lh("t8",0x40,"s1"))          # gid (s1 not bumped here either)
    emit(andi("t8","t8",0xff))
    emit(lui("at",(LSH_TBL>>16)&0xffff))
    emit(ori("at","at",LSH_TBL&0xffff))
    emit(addu("at","at","t8"))
    emit(lbu("t8",0,"at"))            # leftshift
    emit(subu("v1","v1","t8"))        # penX -= leftshift
    emit(j(0x30801C)); emit(nop())
    return w,pc
cgs,cgs_end=chargen_shift(cga_end)
print("\n=== CHARGEN DRAW-SHIFT @0x%X ; hook 0x308018 -> j; replaces lh v1,0x1cc(sp) ==="%cga_end)
disp(cgs,cga_end)

# ---- Chargen SUM-CENTERING (Stage 3): replace count*12 @ 0x307FBC..0x307FC4 with SUM/2.
#   At 0x307FB8: v0 = lh 0x1cc(sp) (base). a1 = count (we ignore). Reserve = SUM/2.
#   Walk s3+0x40 (32 max, -1 term) summing ADV; v0 -= SUM>>1; sh v0,0x1cc(sp); ret 0x307FD8.
#   Hook 0x307FBC (sll a0,a1,1) -> j cave. Original 0x307FBC..0x307FD4 (sll/addu/sll/sext/sext/subu/sh)
#   replaced. v0 already = base (loaded 0x307FB8). s3 live. scratch a0,v1,at,t8,t9.
def chargen_center(pc0):
    w=[];pc=pc0
    def emit(x):
        nonlocal pc; w.append(x); pc+=4
    emit(addiu("t8","s3",0x40))       # ptr
    emit(addiu("t9","zero",0))        # SUM
    emit(addiu("a0","zero",-1))       # term
    emit(lui("v1",(ADV_TBL>>16)&0xffff))
    emit(ori("v1","v1",ADV_TBL&0xffff))
    loop=pc
    emit(lh("at",0,"t8"))             # glyph
    beq_pc=pc; bidx=len(w); emit(0)   # beq at,a0,done
    emit(nop())
    emit(andi("at","at",0xff))
    emit(addu("at","v1","at"))
    emit(lbu("at",0,"at"))
    emit(addu("t9","t9","at"))
    emit(addiu("t8","t8",2))
    emit(j(loop)); emit(nop())
    done=pc
    w[bidx]=beq("at","a0",done,beq_pc)
    emit(Rt(0,"t9","t9",1,0x02))      # srl t9,t9,1  (SUM/2)
    emit(subu("v0","v0","t9"))        # v0 = base - SUM/2
    emit(sh("v0",0x1cc,"sp"))
    emit(j(0x307FD8)); emit(nop())
    return w,pc
cgc,cgc_end=chargen_center(cgs_end)
print("\n=== CHARGEN SUM-CENTER @0x%X ; hook 0x307FBC -> j; replaces 0x307FBC..0x307FD4 ; ret 0x307FD8 ==="%cgs_end)
disp(cgc,cgs_end)
print("\nALL caves end at VA 0x%X (region base 0x4B0E00, used 0x%X bytes)"%(cgc_end,cgc_end-0x4B0E00))
print("Free region 0x4B0DF0..0x4B27F0 = 6656B; used %d B -> OK"%(cgc_end-0x4B0E00))

print("\n\n############ FINAL WORD LISTS FOR patch_exe.py ############")
def words_hex(w): return '[' + ', '.join('0x%08X'%x for x in w) + ']'
print("NS_A (0x4B0E00):"); print(words_hex(nsA))
print("NS_B (0x4B0E50):"); print(words_hex(nsB))
print("CG_ADV (0x4B0EA0):"); print(words_hex(cga))
print("CG_SHIFT (0x4B0EC8):"); print(words_hex(cgs))
print("CG_CENTER (0x4B0EF0):"); print(words_hex(cgc))
print()
print("HOOKS:")
print(" narr ctr A: VA 0x305988 file 0x%X  := j 0x4B0E00 = 0x%08X ; delay 0x30598C nop"%(0x305988-0xFFF80, j(0x4B0E00)))
print(" narr ctr B: VA 0x3059F8 file 0x%X  := j 0x4B0E50 = 0x%08X ; delay 0x3059FC nop"%(0x3059F8-0xFFF80, j(0x4B0E50)))
print(" cg adv    : VA 0x308040 file 0x%X  := j 0x4B0EA0 = 0x%08X ; delay 0x308044 unchanged(orig sh)"%(0x308040-0xFFF80, j(0x4B0EA0)))
print(" cg shift  : VA 0x308018 file 0x%X  := j 0x4B0EC8 = 0x%08X ; delay 0x30801C unchanged"%(0x308018-0xFFF80, j(0x4B0EC8)))
print(" cg center : VA 0x307FBC file 0x%X  := j 0x4B0EF0 = 0x%08X ; delay 0x307FC0 nop"%(0x307FBC-0xFFF80, j(0x4B0EF0)))
print()
print("file offsets (cave bases):")
for nm,va in [('NS_A',0x4B0E00),('NS_B',0x4B0E50),('CG_ADV',0x4B0EA0),('CG_SHIFT',0x4B0EC8),('CG_CENTER',0x4B0EF0)]:
    print("  %s VA 0x%X -> file 0x%X"%(nm,va,va-0xFFF80))
