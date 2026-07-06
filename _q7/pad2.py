import struct
exe=open(r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78",'rb').read()
# how far does zero pad extend from 0x3D6680?
start=0x3D6680
end=start
while end<len(exe) and exe[end]==0: end+=1
print(f"zero run: 0x{start:X} .. 0x{end:X} = {end-start} bytes")
# cave layout file offsets
print("cave1 0x3D6680 .. 0x%X (68B)"%(0x3D6680+68))
print("cave2 0x3D66E0 .. 0x%X (48B)"%(0x3D66E0+48))
print("cave3 0x3D6720 .. 0x%X (108B)"%(0x3D6720+108))
