import sys
sys.stdout.reconfigure(encoding='utf-8')

# Active party glyph indices (R2100 page-0 raw)
active = {
 'slot0 BABA': [34,33,34,33],
 'slot1': [193,194,232,205],
 'slot2': [254,205,202,93],
 'slot3': [196,254,238],
 'slot4': [220,232,93,245,193],
 'slot5': [254,233,211,233,205],
}
pool = {
 'pool0': [232,252,268],
 'pool1': [149,164,177,160],
 'pool2': [132,177,168,170,160],
 'pool3': [138,174,173,163,164],
 'pool4': [136,177,168,178],
 'pool5': [211,265,233,243,93],
 'pool6': [128,174,168],
 'pool7': [257,233,241,231,93,217],
 'pool8': [257,233,208,238],
 'pool9': [273,267,194,233],
 'pool10':[148,171,168],
 'pool11':[140,164,171,160,173,168,164],
}
# ASCII hypothesis for active: char = id+32 -> A=33 char='A'(65)? 33+32=65 yes
def ascii_active(ids):
    s=''
    for v in ids:
        c=v+32
        s+= chr(c) if 32<=c<127 else f'[{v}]'
    return s
# pool low-range: maybe char = id-96 -> 'A' if id=161? no. try id-95
def ascii_pool(ids, base):
    s=''
    for v in ids:
        c=v-base
        s+= chr(c) if 32<=c<127 else f'[{v}]'
    return s

print("ACTIVE (char=id+32):")
for k,v in active.items():
    print(f"  {k}: {ascii_active(v)}")

print("\nPOOL low-range trials:")
for base in [96,95,97,64,63]:
    print(f" base {base}:")
    for k,v in pool.items():
        print(f"   {k}: {ascii_pool(v,base)}")
