import sys
sys.stdout.reconfigure(encoding='utf-8')
try:
    from PIL import Image
except Exception as e:
    print("noPIL", e); sys.exit(0)
im=Image.open('build/recon_cine/extract/overflowbartalk__shot.png').convert('L')
w,h=im.size
print('size',w,h)
px=im.load()
# row brightness profile in the dialogue region (bottom third)
rows=[]
for y in range(h):
    s=0
    for x in range(0,w,2):
        s+=px[x,y]
    rows.append(s//(w//2))
# print profile for bottom area
for y in range(int(h*0.55), h):
    bar='#'*(rows[y]//6)
    print('%3d %3d %s'%(y, rows[y], bar))
