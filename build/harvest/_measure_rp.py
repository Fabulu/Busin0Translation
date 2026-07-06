from PIL import Image
im=Image.open("C:/programmieren/wizardrytranslation/build/harvest/_requestperfect/Screenshot.png").convert("RGB")
W,H=im.size
print("size",W,H)
px=im.load()
# Body text is light glyphs on dark parchment. Find dark text columns per row band.
# Image is 320x240-ish? check
# We'll scan a body row band and detect glyph column centers by ink (text appears DARK here on light parchment? It's light text). 
# Determine: sample brightness histogram in body region
import statistics
def rowscan(y0,y1,label):
    cols=[]
    for x in range(W):
        ink=0
        for y in range(y0,y1):
            r,g,b=px[x,y]
            lum=(r+g+b)/3
            # body text appears lighter than parchment? Actually text is light-gray on tan. Use distance from tan.
            if lum<90:  # dark
                ink+=1
        cols.append(ink)
    # find runs of ink>threshold
    runs=[]
    inrun=False;s=0
    for x in range(W):
        if cols[x]>=2 and not inrun: inrun=True;s=x
        elif cols[x]<2 and inrun: inrun=False;runs.append((s,x-1))
    print(label, "runs:", [(a,b) for a,b in runs][:30])
    centers=[(a+b)//2 for a,b in runs]
    if len(centers)>2:
        d=[centers[i+1]-centers[i] for i in range(len(centers)-1)]
        print("   centers",centers[:20])
        print("   gaps",d[:20])
rowscan(int(H*0.30),int(H*0.36),"body-line1")
rowscan(int(H*0.40),int(H*0.46),"body-line3")
