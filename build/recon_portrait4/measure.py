import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np
E='build/recon_portrait4/extract/'
for n in ['ladyknightnoportrait','Tooearlylinewrap','nshadymanand4linesinsteadof3','nosister','Toolongspaces','Ithinkguyshouldshowuphere']:
    im=Image.open(E+n+'__shot.png').convert('RGB')
    a=np.array(im)
    print(n, im.size)
