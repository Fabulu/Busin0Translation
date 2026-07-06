from PIL import Image
im=Image.open("C:/programmieren/wizardrytranslation/build/recon_tri/extract/veraisjapanese__shot.png").convert("RGB")
print(im.size)
# party bar lower area
w,h=im.size
crop=im.crop((0,int(h*0.78),w,h))
crop=crop.resize((crop.width*4,crop.height*4),Image.NEAREST)
crop.save("C:/programmieren/wizardrytranslation/build/recon_vera2/synth/bar_zoom.png")
