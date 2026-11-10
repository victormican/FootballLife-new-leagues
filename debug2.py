import json

with open("patches/layout.json", encoding="utf-8") as f:
    L = json.load(f)
print(L["arrays"][:5])
