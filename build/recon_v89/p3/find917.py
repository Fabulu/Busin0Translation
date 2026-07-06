import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open("data/type2_translated/batch_01.json", encoding="utf-8"))
# structure?
print("top type:", type(d).__name__)
if isinstance(d, dict):
    print("keys sample:", list(d.keys())[:5])
# find entries for resource 1197 msg 917
def walk(obj):
    found=[]
    if isinstance(obj, list):
        for e in obj:
            if isinstance(e, dict):
                r = e.get("resource") or e.get("res") or e.get("resource_id")
                m = e.get("msg_index", e.get("msg", e.get("index")))
                if (r in (1197,"1197")) and str(m)=="917":
                    found.append(e)
        return found
    return found
res = walk(d)
for e in res:
    print(json.dumps(e, ensure_ascii=False, indent=2))
print("count matched:", len(res))
