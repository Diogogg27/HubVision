# -*- coding: utf-8 -*-
"""
Build da biblioteca v2 -> js/prompts_library.js (dataset do grid).
- Le coleta_v2_manifest.json
- Limpa prompt (clean_text)
- Detecta ingles; traduz nao-ingles via Google Translate (cache incremental)
- Copia imagens para prompts_library/<grupo>/<file>.jpg
- Gera js/prompts_library.js + js/prompts_library_translations.json (cache)
"""
import os
import re
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"P:\LandingPage-PromptHub"
MANIFEST = os.path.join(BASE, ".freebuff", "coleta_v2_manifest.json")
IMG_DST = os.path.join(BASE, "prompts_library")
LIB_JS = os.path.join(BASE, "js", "prompts_library.js")
TR_CACHE = os.path.join(BASE, ".freebuff", "library_v2_translations.json")

GT_URL = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q="

BOILER = [
    r"^\s*0%\s*$", r"^\s*\d+K?\s*$", r"^\s*\d{1,2}:\d{2}\s*$",
    r"Leave a comment.*", r"Subscribe!.*", r"Boost.*", r"Join:\s*@\S+.*",
    r"Made with Inside.*", r"^[\s✦*\-–—·.]+$",
    r"^\s*Views?\s*$", r"^\s*Replies?\s*$",
    r"^\s*Чат\b.*", r"^\s*[\d.,]+\s*К?\s*$",
]

NON_LATIN = r"[\u0400-\u04FF\u0370-\u03FF\u0590-\u05FF\u0600-\u06FF\u0900-\u097F\u4E00-\u9FFF\uAC00-\uD7AF]"


def clean_text(text):
    if not text:
        return ""
    t = text.replace("\u00a0", " ")
    lines = []
    for ln in t.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if any(re.search(p, ln, flags=re.IGNORECASE) for p in BOILER):
            continue
        lines.append(ln)
    t = " ".join(lines)
    t = re.sub(r"#\w+", "", t)
    t = re.sub(r"@\w+", "", t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"t\.me/\S+", "", t)
    t = re.sub(r"tg://\S+", "", t)
    t = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2190-\u21FF\u2B00-\u2BFF\uFE0F\u2022]", "", t)
    t = re.sub(r"[\"']?[✦✧❀❁❃❆❈❉❊❋*•·▪◦▫►◆■□]+\s*", " ", t)
    t = re.sub(r"\s+", " ", t)
    t = t.strip(" .,;:!?–—-()[]\"'«»")
    return t


def is_english(text):
    if re.search(NON_LATIN, text):
        return False
    alpha = sum(1 for ch in text if ch.isalpha())
    if alpha == 0:
        return True
    ascii_alpha = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    return ascii_alpha / alpha > 0.85


def is_junk(text):
    t = text.strip().lower()
    if len(t) < 20:
        return True
    if t.count("http") >= 2 or "t.me" in t:
        return True
    if sum(1 for ch in t if ch.isalnum()) < 10:
        return True
    return False


def translate(q):
    url = GT_URL + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=25).read())
    return "".join(seg[0] for seg in data[0] if seg and seg[0]).strip()


def main():
    items = json.load(open(MANIFEST, encoding="utf-8"))
    print("manifest:", len(items))

    cache = {}
    if os.path.exists(TR_CACHE):
        try:
            c = json.load(open(TR_CACHE, encoding="utf-8"))
            for k, v in c.items():
                if v and not re.search(NON_LATIN, v):
                    cache[k] = v
        except Exception:
            cache = {}
    print("cache:", len(cache))

    todos = []
    for it in items:
        cleaned = clean_text(it["prompt_original"])
        key = cleaned[:200]
        if key in cache:
            it["en"] = cache[key]
        elif not cleaned or is_junk(cleaned):
            it["en"] = ""
        elif is_english(cleaned):
            it["en"] = cleaned
        else:
            it["en"] = None
            it["_key"] = key
        todos.append(it)

    to_translate = [it for it in todos if it["en"] is None]
    print("para traduzir:", len(to_translate))

    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(translate, it["_key"]): it for it in to_translate}
        for fut in as_completed(futs):
            it = futs[fut]
            try:
                en = fut.result()
                it["en"] = en if en else ""
            except Exception:
                it["en"] = ""
            done += 1
            if done % 150 == 0:
                print(f"  {done}/{len(to_translate)} | {time.time()-t0:.0f}s", flush=True)

    # atualiza cache
    for it in todos:
        key = it.pop("_key", None)
        if key:
            cache[key] = it["en"]
    json.dump(cache, open(TR_CACHE, "w", encoding="utf-8"), ensure_ascii=False)

    # copia imagens
    os.makedirs(IMG_DST, exist_ok=True)
    final = []
    for it in todos:
        en = it["en"]
        if not en:
            continue
        src = os.path.join(BASE, "PromptHub_coleta_v2", it["grupo"], it["file"] + ".jpg")
        dst_dir = os.path.join(IMG_DST, it["grupo"])
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, it["file"] + ".jpg")
        if os.path.exists(src):
            import shutil
            shutil.copy(src, dst)
        else:
            continue
        final.append({
            "img": "prompts_library/" + it["grupo"] + "/" + it["file"] + ".jpg",
            "prompt": en,
            "grupo": it["grupo"],
            "categoria": it["categoria"],
            "modelo": it["modelo"],
            "link": it["link_publico"],
            "data": it["data"],
        })

    # gera js dataset
    js = "window.PROMPTS_LIBRARY = %s;" % json.dumps(final, ensure_ascii=False)
    with open(LIB_JS, "w", encoding="utf-8") as f:
        f.write(js)

    print("final:", len(final), "| ignorados:", len(items) - len(final),
          "| com modelo:", sum(1 for x in final if x["modelo"]),
          "| %.0fs" % (time.time() - t0))
    from collections import Counter
    print("por grupo:", dict(Counter(x["grupo"] for x in final)))


if __name__ == "__main__":
    main()