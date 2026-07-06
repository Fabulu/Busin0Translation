import sys, struct
sys.path.insert(0, r'C:\programmieren\wizardrytranslation\build\_recon_2f2490')
from dec import dec, VA_BASE, exe
start = int(sys.argv[1], 16)
n = int(sys.argv[2]) if len(sys.argv) > 2 else 60
va = start
for _ in range(n):
    w = struct.unpack('<I', exe[va - VA_BASE:va - VA_BASE + 4])[0]
    print('%08X  %s' % (va, dec(w, va)))
    va += 4
