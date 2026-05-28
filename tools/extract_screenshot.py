import zipfile
z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
with open('C:/Programmieren/wizardrytranslation/ramdumps/intro_screenshot.png', 'wb') as f:
    f.write(z.read('Screenshot.png'))
print('Screenshot extracted')
