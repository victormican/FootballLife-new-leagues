import glob, os
for f in glob.glob(r"C:\Users\viarm\AppData\Local\Temp\opencode\cpktext\*\string\all.str"):
    b = open(f, "rb").read()
    print(os.path.dirname(os.path.dirname(f)), len(b), b[:48].hex(" "))
    for enc in ("utf-16-le", "utf-8", "latin1"):
        try:
            t = b.decode(enc, "ignore")
        except Exception:
            continue
        i = t.find("FIFA Club World Cup")
        if i < 0: i = t.find("Club World Cup")
        if i >= 0:
            print("   found with", enc, "at", i, repr(t[max(0,i-40):i+40]))
            break
