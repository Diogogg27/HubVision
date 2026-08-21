# -*- coding: utf-8 -*-
"""
Traduz e refina todos os pares do pool (PromptHub_coleta) para ingles.
- Limpa lixo do Telegram (contadores, "0%", hashtags, mencoes, URLs, emojis, boilerplate)
- Traduz textos nao-ingleses via endpoint gratuito do Google Translate (thread pool)
- Cache incremental em .freebuff/translated_pool.json (seguro para interromper/retomar)

Saida: .freebuff/translated_pool.json — lista de dicts:
  folder, file, jpg, w, h, dim, text (original limpo), en (texto final em ingles)
"""
import os
import re
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"P:\LandingPage-PromptHub"
POOL = os.path.join(BASE, ".freebuff", "pool_inventory.json")
OUT = os.path.join(BASE, ".freebuff", "translated_pool.json")

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
        skip = any(re.search(p, ln, flags=re.IGNORECASE) for p in BOILER)
        if not skip:
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
    # qualquer script nao-latino -> precisa traduzir
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
    pairs = json.load(open(POOL, encoding="utf-8"))
    print("pool:", len(pairs))

    # carrega cache existente (chave limpa -> traduzida)
    cache = {}
    if os.path.exists(OUT):
        try:
            for it in json.load(open(OUT, encoding="utf-8")):
                # nao reaproveita traducoes que ainda contem script nao-latino
                if it["en"] and not re.search(NON_LATIN, it["en"]):
                    cache[it["text"][:200]] = it["en"]
        except Exception:
            cache = {}
    print("cache:", len(cache))

    todos = []
    for p in pairs:
        cleaned = clean_text(p["text"])
        key = cleaned[:200]
        if key in cache:
            p["en"] = cache[key]
        elif not cleaned or is_junk(cleaned):
            p["en"] = ""
        elif is_english(cleaned):
            p["en"] = cleaned
        else:
            p["en"] = None  # precisa traduzir
            p["_key"] = key
        todos.append(p)

    to_translate = [p for p in todos if p["en"] is None]
    print("para traduzir:", len(to_translate))

    t0 = time.time()
    done = 0
    fails = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(translate, p["_key"]): p for p in to_translate}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                p["en"] = fut.result()
                if not p["en"]:
                    p["en"] = ""
            except Exception as e:
                fails.append(p)
                p["en"] = ""
            done += 1
            if done % 150 == 0:
                print(f"  {done}/{len(to_translate)} | {time.time()-t0:.0f}s", flush=True)

    for p in todos:
        p.pop("_key", None)
    json.dump(todos, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    n_tr = len(to_translate) - len(fails)
    print("final:", len(todos), "| traduzidas:", n_tr,
          "| falhas:", len(fails),
          "| vazias/junk:", sum(1 for p in todos if not p["en"]),
          f"| {time.time()-t0:.0f}s")
    if fails:
        print("exemplos de falha:")
        for p in fails[:5]:
            print("  ", p["text"][:80])


if __name__ == "__main__":
    main()
