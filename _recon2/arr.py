import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def u32(m,va): return struct.unpack('<I',m[va:va+4])[0]
work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')

def fn(va):
    return f"0x{va:08X}"

base=0x578C80
print("menuobj record array (stride 0x14): +0x00=next +0x04=? +0x08=handler +0x0C=ctx +0x10=?")
for tag,p in [('work',work),('froz',froz)]:
    cur=u32(p,0x4FEDC0)
    print(f"\n=== {tag}: active=0x{cur:08X} ===")
    for rec in range(base, base+0x14*8, 0x14):
        marker=' <== ACTIVE' if rec==cur else ''
        vals=[u32(p,rec+o) for o in (0,4,8,0xC,0x10)]
        print(f"  rec 0x{rec:08X}: nxt={vals[0]:08X} a={vals[1]:08X} hdl={vals[2]:08X} ctx={vals[3]:08X} e={vals[4]:08X}{marker}")
