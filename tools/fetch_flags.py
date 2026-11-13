import io
import json
import os
import time
import urllib.error
import urllib.request

from PIL import Image

MAP = {
    "MARTINIQUE": (96, "Martinique"),
    "GUADELOUPE": (97, "Guadeloupe"),
    "FRENCH GUIANA": (99, "French Guiana"),
    "SAINT MARTIN": (100, "Collectivity of Saint Martin"),
    "SINT MAARTEN": (101, "Sint Maarten"),
    "BONAIRE": (102, "Bonaire"),
    "GUNA": (267, "Guna people"),
    "HAWAII": (251, "Hawaii"),
    "CASCADIA": (269, "Cascadia (bioregion)"),
    "INDIGENOUS ALBERTA": (270, None),
    "CATALONIA": (118, "Catalonia"),
    "PADANIA": (123, "Padania"),
    "BASQUE COUNTRY": (126, "Basque Country (autonomous community)"),
    "GALICIA": (138, "Galicia (Spain)"),
    "BRITTANY": (141, "Brittany"),
    "CORSICA": (142, "Corsica"),
    "SICILY": (143, "Sicily"),
    "SARDINIA": (154, "Sardinia"),
    "OCCITANIA": (155, "Occitania"),
    "CORNWALL": (156, "Cornwall"),
    "PROVENCE": (157, "Provence"),
    "TWO SICILIES": (158, "Kingdom of the Two Sicilies"),
    "ABKHAZIA": (160, "Abkhazia"),
    "SOUTH OSSETIA": (173, "South Ossetia"),
    "TRANSNISTRIA": (174, "Transnistria"),
    "NORTHERN CYPRUS": (175, "Northern Cyprus"),
    "SAPMI": (177, "Sapmi"),
    "ROMANI": (178, "Flag of the Romani people"),
    "GREENLAND": (179, "Greenland"),
    "ELLAN VANNIN": (180, "Isle of Man"),
    "GUERNSEY": (181, "Guernsey"),
    "JERSEY": (182, "Jersey"),
    "GOZO": (183, "Gozo"),
    "AGRO PONTINO": (185, None),
    "TICINO": (186, "Canton of Ticino"),
    "CHAMERIA": (187, None),
    "CUMANN SACAIRE GAEILGE": (188, None),
    "KARPATALJA": (233, "Carpathian Ruthenia"),
    "RAETIA": (242, "Raetia"),
    "SZEKELY LAND": (243, "Szekely Land"),
    "SOMALILAND": (244, "Somaliland"),
    "WESTERN SAHARA": (246, "Western Sahara"),
    "KABYLIE": (247, "Kabylia"),
    "MAYOTTE": (248, "Mayotte"),
    "ARTSAKH": (249, "Republic of Artsakh"),
    "KURDISTAN": (251, "Kurdistan"),
    "TAMIL EELAM": (252, "Tamil Eelam"),
    "TIBET": (253, "Tibet"),
    "EAST TURKESTAN": (254, "East Turkestan"),
    "GIRL POWER": (255, None),
    "HMONG": (256, "Hmong people"),
    "KASHMIR": (257, "Kashmir"),
    "KHALISTAN": (258, "Khalistan"),
    "PANJAB": (259, "Punjab, India"),
    "PALESTINE REFUGEE": (261, "Palestine"),
    "ROJAVA": (262, "Autonomous Administration of North and East Syria"),
    "MAPUCHE": (263, "Mapuche"),
    "AYMARA": (264, "Aymara people"),
    "RAPA NUI": (265, "Rapa Nui people"),
    "SAO PAULO": (266, "Sao Paulo (state)"),
    "WALLIS AND FUTUNA": (271, "Wallis and Futuna"),
    "NIUE": (272, "Niue"),
    "WEST PAPUA": (273, "West Papua (region)"),
}

OUT = r"D:\SP Football Life 2026 - copia\SiderAddons\livecpk\_FL26Sud\common\render\symbol\flag"
os.makedirs(OUT, exist_ok=True)

UA = {
    "User-Agent": "flag-fetcher/1.0 (https://github.com/victormican/FootballLife-new-leagues; educational)"
}


def fetch(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30
    ).read()


def summary_img(title):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title.replace(" ", "_")
    for attempt in range(3):
        try:
            d = json.loads(fetch(url))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(12 * (attempt + 1))
                continue
            return "ERR summary " + str(e)
        except Exception as e:
            return "ERR summary " + str(e)
    t = d.get("thumbnail") or {}
    src = t.get("source")
    if not src:
        src = (d.get("originalimage") or {}).get("source")
    return src


ok, bad = [], []
for name, (cid, title) in MAP.items():
    path = os.path.join(OUT, "flag_%d.png" % cid)
    if os.path.exists(path):
        ok.append(name)
        continue
    if title is None:
        bad.append((name, "skip (no article)"))
        continue
    src = summary_img(title)
    if not src or src.startswith("ERR"):
        bad.append((name, src or "no image"))
    else:
        try:
            raw = fetch(src)
            img = (
                Image.open(io.BytesIO(raw))
                .convert("RGBA")
                .resize((256, 256), Image.LANCZOS)
            )
            img.save(path)
            ok.append(name)
        except Exception as e:
            bad.append((name, "DL " + str(e)))
    time.sleep(1.5)

print("OK %d:" % len(ok))
for n in ok:
    print("  ", n)
print("FALLO %d:" % len(bad))
for n, r in bad:
    print("  ", n, "->", r)
