import json

with open("patches/layout.json", encoding="utf-8") as f:
    L = json.load(f)
for a in L["arrays"]:
    es = a.get("extra_sites", "null")
    print("%s: extra_sites = %s" % (a["name"], es))
