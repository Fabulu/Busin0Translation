import sys, os, json, struct, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,"C:/programmieren/wizardrytranslation/tools")
import patch_section1_offsets as P
# Need msg_translations for R1197. Find them in data/type2_translated
trans={}
for fp in glob.glob("C:/programmieren/wizardrytranslation/data/type2_translated/batch_*.json"):
    try: d=json.load(open(fp,encoding="utf-8"))
    except: continue
    # structure unknown; look for 1197
    s=json.dumps(d)
    if '"1197"' in s or "1197" in s:
        # try to find
        for k in d:
            if str(k)=="1197" or k=="R1197":
                trans[1197]=d[k]
print("found translation for 1197?", 1197 in trans)
# Regardless, run inject_and_patch with whatever messages exist (empty -> identity? )
raw_dir="C:/programmieren/wizardrytranslation/build/packdata_resources_backup"  # pristine source
out_dir="C:/programmieren/wizardrytranslation/build/recon_w2/parked/freshout"
os.makedirs(out_dir,exist_ok=True)
# Build msg map: try to load from where build_v9 loads it
