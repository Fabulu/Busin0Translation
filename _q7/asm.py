def R(rs,rt,rd,sa,f): return (0<<26)|(rs<<21)|(rt<<16)|(rd<<11)|(sa<<6)|f
def I(op,rs,rt,imm): return (op<<26)|(rs<<21)|(rt<<16)|(imm&0xFFFF)
def J(op,tgt): return (op<<26)|((tgt>>2)&0x03FFFFFF)
REG={'zero':0,'at':1,'v0':2,'v1':3,'a0':4,'a1':5,'a2':6,'a3':7,'t0':8,'t1':9,'t2':10,'t3':11,'t8':24,'t9':25,'gp':28,'sp':29,'s0':16,'s1':17,'s2':18,'s3':19,'s4':20,'s5':21}
def r(n): return REG[n]
# instructions
def lw(rt,off,rs): return I(0x23,r(rs),r(rt),off)
def lh(rt,off,rs): return I(0x21,r(rs),r(rt),off)
def lhu(rt,off,rs): return I(0x25,r(rs),r(rt),off)
def lbu(rt,off,rs): return I(0x24,r(rs),r(rt),off)
def sh(rt,off,rs): return I(0x29,r(rs),r(rt),off)
def addiu(rt,rs,imm): return I(0x09,r(rs),r(rt),imm)
def li(rt,imm): return I(0x09,0,r(rt),imm)
def lui(rt,imm): return I(0x0F,0,r(rt),imm)
def srl(rd,rt,sa): return R(0,r(rt),r(rd),sa,0x02)
def sra(rd,rt,sa): return R(0,r(rt),r(rd),sa,0x03)
def sll(rd,rt,sa): return R(0,r(rt),r(rd),sa,0x00)
def addu(rd,rs,rt): return R(r(rs),r(rt),r(rd),0,0x21)
def subu(rd,rs,rt): return R(r(rs),r(rt),r(rd),0,0x23)
def move(rd,rs): return R(r(rs),0,r(rd),0,0x21)
def bne(rs,rt,rel): return I(0x05,r(rs),r(rt),rel)  # rel in words
def beq(rs,rt,rel): return I(0x04,r(rs),r(rt),rel)
def bltz(rs,rel): return I(0x01,r(rs),0,rel)
def b(rel): return I(0x04,0,0,rel)
def jj(tgt): return J(0x02,tgt)
def nop(): return 0
def dump(name,lst,base):
    print(f"--- {name} @0x{base:08X} ---")
    for i,w in enumerate(lst):
        print(f"  0x{w:08X},  # +{i*4:#x}")

GP_MODE = -0x62d8  # lw at,-0x62d8(gp)
CAVE1=0x4D6600; CAVE2=0x4D6660; CAVE3=0x4D66A0

# ===== CAVE1 (advance) -> falls to STORE then j 0x308048 =====
# layout (word indices):
# 0 lw   at,-0x62d8(gp)
# 1 lh   v1,0x40(s1)
# 2 li   t0,5
# 3 bne  at,t0,STOCK     ; STOCK at index? compute
# 4 srl  v1,v1,8         (delay)
# 5 lui  t0,0x4C
# 6 addu t0,t0,v1
# 7 lbu  t0,0x7564(t0)
# 8 lh   v0,0x1cc(sp)
# 9 addu v0,v0,t0
# 10 b   STORE
# 11 nop  (delay)
# 12 STOCK: lh v0,0x1cc(sp)
# 13 addiu v0,v0,0x18
# 14 STORE: sh v0,0x1cc(sp)
# 15 j 0x308048
# 16 nop
# bne target STOCK = index 12. PC of bne = index3. branch delay -> target = (idx3+1)+rel = idx12 => rel = 12-4 = 8
# b STORE: PC idx10, target idx14 => rel = 14-11 = 3
cave1=[
 lw('at',GP_MODE,'gp'),
 lh('v1',0x40,'s1'),
 li('t0',5),
 bne('at','t0', 8),
 srl('v1','v1',8),
 lui('t0',0x4C),
 addu('t0','t0','v1'),
 lbu('t0',0x7564,'t0'),
 lh('v0',0x1cc,'sp'),
 addu('v0','v0','t0'),
 b(3),
 nop(),
 lh('v0',0x1cc,'sp'),
 addiu('v0','v0',0x18),
 sh('v0',0x1cc,'sp'),
 jj(0x308048),
 nop(),
]
dump("cave1",cave1,CAVE1)

# ===== CAVE2 (draw-shift) -> j 0x30801C. gate: mode==5 else just j back without shift =====
# uses at/t9 only (t0 LIVE). penX in v1 (already loaded at hook via... no, hook REPLACED lh v1,0x1cc(sp))
# hook 0x308018 was `lh v1,0x1cc(sp)`. We replace with j cave2. cave2 must reload v1.
# 0 lw  t9,-0x62d8(gp)   ; mode (use t9 scratch)
# 1 lh  v1,0x1cc(sp)     ; penX (this is the displaced instruction's effect)
# 2 li  t8,5
# 3 bne t9,t8,DONE       ; mode!=5 -> skip shift
# 4 lh  t9,0x40(s1)      (delay) cell
# 5 srl t9,t9,8          ; char-32
# 6 lui at,0x4C
# 7 addu at,at,t9
# 8 lbu at,0x7690(at)    ; LEFTSHIFT
# 9 subu v1,v1,at        ; penX -= leftshift
# 10 DONE: j 0x30801C
# 11 nop
# bne DONE = idx10 ; PC idx3 -> rel = 10-4 = 6
cave2=[
 lw('t9',GP_MODE,'gp'),
 lh('v1',0x1cc,'sp'),
 li('t8',5),
 bne('t9','t8',6),
 lh('t9',0x40,'s1'),
 srl('t9','t9',8),
 lui('at',0x4C),
 addu('at','at','t9'),
 lbu('at',0x7690,'at'),
 subu('v1','v1','at'),
 jj(0x30801C),
 nop(),
]
dump("cave2",cave2,CAVE2)

# ===== CAVE3 (summed centering) -> j 0x307FD8. gate mode==5 else stock count*12 =====
# hook 0x307FBC orig `sll a0,a1,1` (head of count*12). 0x307FC0 orig `addu a0,a0,a1` -> nop.
# We must preserve v1(=count) -> flows to 0x307FE4. a0,a1,a2,a3,t0 scratch here.
# original count*12: a0 = a1*12; then 0x307FC4 sll a0,a0,2 (already after); actually orig seq:
#   sll a0,a1,1 ; addu a0,a0,a1 ; sll a0,a0,2 -> a0 = a1*3*4 = a1*12. then lh v0,0x1cc; subu v0,v0,a0; sh.
# Wait 0x307FB8 lh v0,0x1cc is BEFORE 0x307FBC. Re-examine: 0x307FB8 lh v0; 0x307FBC sll a0,a1,1...0x307FD0 subu v0,v0,a0; 0x307FD4 sh v0,0x1cc.
# cave3 hooks 0x307FBC, returns to 0x307FD8 (past the sh). So cave3 must compute pen and STORE 0x1cc.
# gate:
# 0 lw  t1,-0x62d8(gp)
# 1 li  t2,5
# 2 bne t1,t2,STOCK
# 3 lh  v0,0x1cc(sp)      (delay) ; pen (=0)
# --- chargen summed path ---
# 4 addiu a2,s3,0x40      ; &glyph[0]
# 5 move t0,zero          ; SUM
# 6 lui a0,0x4C
# 7 LOOP: lh a1,0(a2)
# 8 bltz a1,DONE
# 9 srl a3,a1,8           (delay) char-32
# 10 addu a3,a0,a3
# 11 lbu a3,0x7564(a3)
# 12 addu t0,t0,a3
# 13 addiu a2,a2,2
# 14 b LOOP
# 15 nop (delay)
# 16 DONE: sra t0,t0,1    ; SUM/2
# 17 subu v0,v0,t0        ; pen -= SUM/2
# 18 b WRITE
# 19 nop
# 20 STOCK: sll a0,a1,1   ; orig
# 21 addu a0,a0,a1
# 22 sll a0,a0,2          ; a0=a1*12
# 23 subu v0,v0,a0
# 24 WRITE: sh v0,0x1cc(sp)
# 25 j 0x307FD8
# 26 nop
# bne STOCK = idx20; PC idx2 -> rel=20-3=17
# bltz DONE = idx16; PC idx8 -> rel=16-9=7
# b LOOP=idx7; PC idx14 -> rel = 7-15 = -8
# b WRITE=idx24; PC idx18 -> rel=24-19=5
cave3=[
 lw('t1',GP_MODE,'gp'),
 li('t2',5),
 bne('t1','t2',17),
 lh('v0',0x1cc,'sp'),
 addiu('a2','s3',0x40),
 move('t0','zero'),
 lui('a0',0x4C),
 lh('a1',0,'a2'),
 bltz('a1',7),
 srl('a3','a1',8),
 addu('a3','a0','a3'),
 lbu('a3',0x7564,'a3'),
 addu('t0','t0','a3'),
 addiu('a2','a2',2),
 b(-8),
 nop(),
 sra('t0','t0',1),
 subu('v0','v0','t0'),
 b(5),
 nop(),
 sll('a0','a1',1),
 addu('a0','a0','a1'),
 sll('a0','a0',2),
 subu('v0','v0','a0'),
 sh('v0',0x1cc,'sp'),
 jj(0x307FD8),
 nop(),
]
dump("cave3",cave3,CAVE3)
print("\nlens:",len(cave1),len(cave2),len(cave3))
