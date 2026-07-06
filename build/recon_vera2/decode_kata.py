import sys
sys.stdout.reconfigure(encoding='utf-8')
# Active party katakana glyph indices. R2100 page-0 raw indices.
# Vera = ヴェーラ. slot1=[193,194,232,205]. slot4 has 220,232,93,245,193
# These are R2100 atlas glyph IDs. Let's map known katakana from the prompt:
# ア=193, ー=93, バ=254
# slot1 = [193,194,232,205] -> ア ? ? ?
# Need R2100 atlas katakana ordering. Let's check if active katakana base matches
# the recruit pool's KATAKANA entries (pool0,5,7,8,9) which are NOT romanized.
active = {
 'slot1': [193,194,232,205],
 'slot2': [254,205,202,93],
 'slot3': [196,254,238],
 'slot4': [220,232,93,245,193],
 'slot5': [254,233,211,233,205],
}
pool_kata = {
 'pool0': [232,252,268],
 'pool5': [211,265,233,243,93],
 'pool7': [257,233,241,231,93,217],
 'pool8': [257,233,208,238],
 'pool9': [273,267,194,233],
}
# Are active slots a subset/match of pool katakana? Check overlap of index sets
print("Active slot index sets:")
for k,v in active.items(): print(f"  {k}: {sorted(set(v))}")
print("Pool katakana index sets:")
for k,v in pool_kata.items(): print(f"  {k}: {sorted(set(v))}")
