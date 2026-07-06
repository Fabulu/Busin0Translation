import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
E='build/recon_portrait4/extract/'
for n in ['ladyknightnoportrait','nshadymanand4linesinsteadof3']:
    im=Image.open(E+n+'__shot.png').convert('RGB')
    # crop bottom box region, upscale 2x
    c=im.crop((0,370,640,480)).resize((1280,220),Image.NEAREST)
    c.save(f'build/recon_portrait4/{n}_box.png')
    print('saved',n)
