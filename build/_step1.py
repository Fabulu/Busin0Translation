import json

with open('data/msg_glyph_map.json', 'r', encoding='utf-8') as f:
    master = json.load(f)
original_count = len(master)
proposals = {}
def add(g, c, conf, agent):
    gid = str(g)
    if gid not in proposals: proposals[gid] = []
    proposals[gid].append((c, conf, agent))
print('Setup done, loading proposals...')
