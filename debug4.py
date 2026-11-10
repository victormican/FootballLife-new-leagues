#!/usr/bin/env python
import json, sys

data = open("patches/layout.json", encoding="utf-8").read()
L = json.loads(data)
print("tipo:", type(L))
print("claves:", list(L.keys()))
arrs = L["arrays"]
print("num arrays:", len(arrs))
for i in range(min(5, len(arrs))):
    a = arrs[i]
    print(
        "arr",
        i,
        type(a).__name__,
        "[:60]" if isinstance(a, str) else "keys:",
        a[:60] if isinstance(a, str) else list(a.keys()),
    )
