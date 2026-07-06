import sys,json,os,re
sys.path.insert(0,"build")
from _shard3_classifier import get_groups, classify_group, decode_message
BASE="C:/Programmieren/wizardrytranslation"

IDS=[912,913,914,915,916,918,922,923,924,925,926,928,930,931,1054,1055,1056,1058,1059,1060,1062,1063,1064,1065,1066,1067,1068,1069,1070,1071,1074,1076,1078,1079,1080,1082,1085,1086,1087,1088,1089,1090,1092,1094,1095,1096,1100,1103,1106,1107,1108,1116,1117,1118,1120,1124,1126,1127,1128,1132,1134,1137,1142,1148,1152,1154,1156,1157,1158,1159,1162,1187,1189,1192,1195,1214,1358,1359,1360,1361,1362,1363,1365,1366,1367]

def ascii_gloss(text):
    out=[]
    for ch in text:
        o=ord(ch)
        out.append(ch if 32<=o<127 else '.')
    return re.sub(r'\s+',' ',"".join(out)).strip()[:80]

results=[]
jp_lines=[]
for rid in IDS:
    gs=get_groups(rid)
    if gs is None:
        results.append({"resource":rid,"kind":"undecodable","dialogueMsgCount":0,"sample":"","notes":"file missing/too small"})
        continue
    if gs==[]:
        results.append({"resource":rid,"kind":"binary","dialogueMsgCount":0,"sample":"","notes":"no valid sec2 (binary)"})
        continue
    dlg=[]
    nonempty=0
    for gi,g in enumerate(gs):
        if not g: continue
        nonempty+=1
        isd,decoded,jpn,tg=classify_group(g)
        if isd: dlg.append((gi,decoded))
    dc=len(dlg)
    if dc==0:
        kind="binary"
    elif dc < nonempty*0.5 and (nonempty-dc)>5:
        kind="mixed"
    else:
        kind="dialogue"
    samp=ascii_gloss(dlg[0][1]) if dlg else ""
    results.append({"resource":rid,"kind":kind,"dialogueMsgCount":dc,"sample":samp,"notes":f"{nonempty} nonempty groups"})
    if dlg:
        jp_lines.append(f"=== R{rid} ({kind}, {dc} dialogue groups, {nonempty} nonempty) ===")
        for gi,dec in dlg[:4]:
            jp_lines.append(f"  [g{gi}] {dec[:160]}")
        jp_lines.append("")

with open(BASE+"/build/_shard3_jp_samples.txt","w",encoding="utf-8") as f:
    f.write("\n".join(jp_lines) if jp_lines else "(no dialogue found in shard 3 untranslated range)")

print(f"{'RID':>5} {'KIND':<11} {'DLG':>4}  SAMPLE")
for r in results:
    print(f"{r['resource']:>5} {r['kind']:<11} {r['dialogueMsgCount']:>4}  {r['sample']}")
from collections import Counter
print("\nTOTALS:", dict(Counter(r['kind'] for r in results)))
print("untranslated scanned:", len(IDS))
json.dump(results, open(BASE+"/build/_shard3_results.json","w"), indent=1)
