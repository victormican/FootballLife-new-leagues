import json

with open("patches/layout.json", encoding="utf-8") as f:
    L = json.load(f)
arrs = L["arrays"]
for i in range(min(5, len(arrs))):
    a = arrs[i]
    print(i, type(a).__name__, a[:60] if isinstance(a, str) else list(a.keys()))
