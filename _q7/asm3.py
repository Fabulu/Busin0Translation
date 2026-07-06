def R(rs,rt,rd,sa,f): return (0<<26)|(rs<<21)|(rt<<16)|(rd<<11)|(sa<<6)|f
def I(op,rs,rt,imm): return (op<<26)|(rs<<21)|(rt<<16)|(imm&0xFFFF)
def J(op,tgt): return (op<<26)|((tgt>>2)&0x03FFFFFF)
REG={'zero':0,'at':1,'v0':2,'v1':3,'a0':4,'a1':5,'a2':6,'a3':7,'t0':8,'t1':9,'t2':10,'t3':11,'gp':28,'sp':29,'s3':19}
def r(n): return REG[n]
def lw(rt,o,rs): return I(0x23,r(rs),r(rt),o)
def lh(rt,o,rs): return I(0x21,r(rs),r(rt),o)
def lbu(rt,o,rs): return I(0x24,r(rs),r(rt),o)
def sh(rt,o,rs): return I(0x29,r(rs),r(rt),o)
def addiu(rt,rs,imm): return I(0x09,r(rs),r(rt),imm)
def li(rt,imm): return I(0x09,0,r(rt),imm)
def lui(rt,imm): return I(0x0F,0,r(rt),imm)
def sltiu(rt,rs,imm): return I(0x0B,r(rs),r(rt),imm)
def srl(rd,rt,sa): return R(0,r(rt),r(rd),sa,0x02)
def sra(rd,rt,sa): return R(0,r(rt),r(rd),sa,0x03)
def sll(rd,rt,sa): return R(0,r(rt),r(rd),sa,0x00)
def addu(rd,rs,rt): return R(r(rs),r(rt),r(rd),0,0x21)
def subu(rd,rs,rt): return R(r(rs),r(rt),r(rd),0,0x23)
def move(rd,rs): return R(r(rs),0,r(rd),0,0x21)
def bne(rs,rt,rel): return I(0x05,r(rs),r(rt),rel)
def beq(rs,rt,rel): return I(0x04,r(rs),r(rt),rel)
def b(rel): return I(0x04,0,0,rel)
def jj(tgt): return J(0x02,tgt)
def nop(): return 0
GP=-0x62d8
# CAVE3 revised: gate mode==5; sum ADV over buffer s3+0x40, stop at -1, skip cells with (cell>>8)>=0x60
# 0  lw   t1,-0x62d8(gp)
# 1  li   t2,5
# 2  bne  t1,t2,STOCK         ; rel -> STOCK
# 3  lh   v0,0x1cc(sp)        (delay) pen(=0)
# 4  addiu a2,s3,0x40
# 5  move t0,zero             ; SUM
# 6  lui  a0,0x4C
# 7 LOOP: lh a1,0(a2)
# 8  li   t3,-1
# 9  beq  a1,t3,DONE          ; rel -> DONE
# 10 srl  a3,a1,8             (delay) char-32 / breakcode
# 11 sltiu at,a3,0x60         ; at=1 if a3<0x60 (real glyph)
# 12 beq  at,zero,SKIP        ; not a glyph -> skip add  ; rel -> SKIP
# 13 addu a3,a0,a3            (delay)
# 14 lbu  a3,0x7564(a3)
# 15 addu t0,t0,a3            ; SUM += ADV
# 16 SKIP: addiu a2,a2,2
# 17 b    LOOP                ; rel -> LOOP
# 18 nop
# 19 DONE: sra t0,t0,1
# 20 subu v0,v0,t0
# 21 b    WRITE
# 22 nop
# 23 STOCK: sll a0,a1,1
# 24 addu a0,a0,a1
# 25 sll  a0,a0,2
# 26 subu v0,v0,a0
# 27 WRITE: sh v0,0x1cc(sp)
# 28 j    0x307FD8
# 29 nop
# bne STOCK=23, PC idx2 -> rel=23-3=20
# beq DONE=19, PC idx9 -> rel=19-10=9
# beq SKIP=16, PC idx12 -> rel=16-13=3
# b LOOP=7, PC idx17 -> rel=7-18=-11
# b WRITE=27, PC idx21 -> rel=27-22=5
cave3=[
 lw('t1',GP,'gp'),
 li('t2',5),
 bne('t1','t2',20),
 lh('v0',0x1cc,'sp'),
 addiu('a2','s3',0x40),
 move('t0','zero'),
 lui('a0',0x4C),
 lh('a1',0,'a2'),
 li('t3',-1),
 beq('a1','t3',9),
 srl('a3','a1',8),
 sltiu('at','a3',0x60),
 beq('at','zero',3),
 addu('a3','a0','a3'),
 lbu('a3',0x7564,'a3'),
 addu('t0','t0','a3'),
 addiu('a2','a2',2),
 b(-11),
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
import sys; sys.path.insert(0,'build/_recon_2f2490'); from dec import dec
base=0x4D66A0
print(f"CAVE3 ({len(cave3)} words) ends file 0x%X"%(0x3D6720+len(cave3)*4))
print("words = [", ','.join("0x%08X"%w for w in cave3), "]")
for i,w in enumerate(cave3):
    print(f"  {base+i*4:08X}: {w:08X}  {dec(w,base+i*4)}")
