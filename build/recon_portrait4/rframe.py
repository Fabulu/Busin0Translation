import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
import numpy as np
im=Image.open('build/recon_portrait4/extract/ladyknightnoportrait__shot.png').convert('RGB')
a=np.array(im).astype(np.int32)
lum=a.mean(axis=2)
# The right ornament: scan box rows y 388-468, look for bright cluster on right side x>500
band=lum[388:468,:]
colmax=band.max(axis=0)
# left ornament at x43-56. Box is symmetric. find right ornament.
right=np.where(colmax[500:]>150)[0]+500
print("right side bright cols (>150) x>500:", right[:40] if len(right) else "none")
# Find the box dark-panel extent: the semi-transparent panel is darker than bg? 
# Use the left ornament center x~50 and assume symmetry about screen center 320
print("left ornament x43-56 center=49.5; mirror about 320 => right ornament ~", 320+(320-49.5))
