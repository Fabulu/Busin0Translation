import struct
EXE = 'C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78'
with open(EXE, 'rb') as f: exe = f.read()
R={0:'zero',1:'at',2:'v0',3:'v1',4:'a0',5:'a1',6:'a2',7:'a3',8:'t0',9:'t1',10:'t2',11:'t3',12:'t4',13:'t5',14:'t6',15:'t7',16:'s0',17:'s1',18:'s2',19:'s3',20:'s4',21:'s5',22:'s6',23:'s7',24:'t8',25:'t9',26:'k0',27:'k1',28:'gp',29:'sp',30:'fp',31:'ra'}
def d(s,e):
 for i in range(s,min(e,len(exe)-3),4):
  w=struct.unpack_from('<I',exe,i)[0];op=(w>>26)&0x3F;rt=(w>>16)&0x1F;rs=(w>>21)&0x1F;rd=(w>>11)&0x1F
  im=w&0xFFFF;si=im if im<0x8000 else im-0x10000;fn=w&0x3F;sa=(w>>6)&0x1F
  rr=lambda x:R.get(x,'r%d'%x)
  if w==0:t='nop'
  elif op==15:t='lui %s,0x%04x'%(rr(rt),im)
  elif op==9:t='addiu %s,%s,%d'%(rr(rt),rr(rs),si)
  elif op==3:t='jal 0x%08x'%((w&0x03FFFFFF)<<2)
  elif op==13:t='ori %s,%s,0x%04x'%(rr(rt),rr(rs),im)
  elif op==43:t='sw %s,%d(%s)'%(rr(rt),si,rr(rs))
  elif op==35:t='lw %s,%d(%s)'%(rr(rt),si,rr(rs))
  elif op==37:t='lhu %s,%d(%s)'%(rr(rt),si,rr(rs))
  elif op==33:t='lh %s,%d(%s)'%(rr(rt),si,rr(rs))
  elif op==36:t='lbu %s,%d(%s)'%(rr(rt),si,rr(rs))
  elif op==40:t='sb %s,%d(%s)'%(rr(rt),si,rr(rs))
  elif op==41:t='sh %s,%d(%s)'%(rr(rt),si,rr(rs))
  elif op==4:t='beq %s,%s,%+d'%(rr(rs),rr(rt),si)
  elif op==5:t='bne %s,%s,%+d'%(rr(rs),rr(rt),si)
  elif op==6:t='blez %s,%+d'%(rr(rs),si)
  elif op==7:t='bgtz %s,%+d'%(rr(rs),si)
  elif op==10:t='slti %s,%s,%d'%(rr(rt),rr(rs),si)
  elif op==12:t='andi %s,%s,0x%04x'%(rr(rt),rr(rs),im)
  elif op==0:
   if fn==33:t='addu %s,%s,%s'%(rr(rd),rr(rs),rr(rt))
   elif fn==45:t='daddu %s,%s,%s'%(rr(rd),rr(rs),rr(rt))
   elif fn==0:t='sll %s,%s,%d'%(rr(rd),rr(rt),sa)
   elif fn==2:t='srl %s,%s,%d'%(rr(rd),rr(rt),sa)
   elif fn==8:t='jr %s'%rr(rs)
   elif fn==9:t='jalr %s'%rr(rs)
   elif fn==42:t='slt %s,%s,%s'%(rr(rd),rr(rs),rr(rt))
   elif fn==37:t='or %s,%s,%s'%(rr(rd),rr(rs),rr(rt))
   elif fn==60:t='dsll32 %s,%s,%d'%(rr(rd),rr(rt),sa)
   elif fn==63:t='dsra32 %s,%s,%d'%(rr(rd),rr(rt),sa)
   elif fn==18:t='mflo %s'%rr(rd)
   elif fn==24:t='mult %s,%s'%(rr(rs),rr(rt))
   else:t='R:%08x fn=%d'%(w,fn)
  elif op==1:t='regimm %08x'%w
  else:t='.w 0x%08x op=%d'%(w,op)
  print('  %06x [%08x]: %s'%(i,i-0x800+0x100000,t))
print('=== 0x080880..0x080c00 ===')
d(0x080880,0x080c00)
print()
print('=== 0x084fc0..0x085300 ===')
d(0x084fc0,0x085300)
print()
print('=== 0x094cc0..0x094e20 ===')
d(0x094cc0,0x094e20)
