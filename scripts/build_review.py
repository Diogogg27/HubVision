# -*- coding: utf-8 -*-
"""
Gera a pagina de revisao visual (_review.html) a partir do pool traduzido.
- Pre-filtra lixo obvio (sinopse de filme, spam de engajamento, textos curtos)
- Agrupa textos com multiplas imagens (albuns) num bloco unico
- Cada item tem botao [X] para marcar invalido; marcas ficam em localStorage

Uso: python scripts/build_review.py
"""
import os
import re
import json
from collections import defaultdict

BASE = r"P:\LandingPage-PromptHub"
POOL = os.path.join(BASE, ".freebuff", "translated_pool.json")
OUT_HTML = os.path.join(BASE, "_review.html")

MOVIE_PAT = re.compile(r"\(\s*(?:19|20)\d{2}\s*\)\s*(?:Dir\.|director|реж)", re.IGNORECASE)
SPAM_PATS = [
    r"in the comments", r"our cart", r"what do you think", r"who has seen it",
    r"subscribe", r"follow", r"like and", r"share this", r"t\.me", r"boost",
    r"telegram", r"comment below", r"thoughts\?", r"opinion", r"vote",
    r"как вам", r"пишите", r"посмотрел", r"коммент",
]

def is_junk(en):
    t = (en or "").strip()
    if len(t) < 25:
        return True
    if re.search(r"\d{2}:\d{2}", t) and len(t) < 90:
        return True
    return False

def is_movie_plot(en):
    t = (en or "")
    if MOVIE_PAT.search(t):
        return True
    # "Dir." sem ano ou descricoes de enredo longas
    if re.search(r"\bDir\.\s+[A-Z]", t) or re.search(r"\bDirector:\s*[A-Z]", t):
        return True
    return False

def is_spam(en):
    t = (en or "").lower()
    return any(re.search(p, t) for p in SPAM_PATS)

def main():
    import sys
    start = end = None
    for a in sys.argv[1:]:
        if a.startswith("--start="):
            start = int(a.split("=", 1)[1])
        elif a.startswith("--end="):
            end = int(a.split("=", 1)[1])
    pool = json.load(open(POOL, encoding="utf-8"))
    items = []
    dropped = {"junk": 0, "movie": 0, "spam": 0}
    for p in pool:
        en = (p.get("en") or "").strip()
        if not en:
            continue
        if is_junk(en):
            dropped["junk"] += 1
            continue
        if is_movie_plot(en):
            dropped["movie"] += 1
            continue
        if is_spam(en):
            dropped["spam"] += 1
            continue
        items.append(p)

    print("itens para revisao:", len(items), "| descartados:", dropped)

    # agrupa por texto exato (EN) -> multiplas imagens
    groups = defaultdict(list)
    for p in items:
        groups[p["en"]].append(p)

    blocks = []
    for text, ps in groups.items():
        blocks.append({"text": text, "items": ps})
    # albuns primeiro (maior risco de pareamento errado)
    blocks.sort(key=lambda b: -len(b["items"]))

    data = []
    idx = 0
    for b in blocks:
        entry = {"i": idx, "text": b["text"], "items": []}
        for p in b["items"]:
            entry["items"].append({
                "folder": p["folder"], "file": p["file"],
                "img": "PromptHub_coleta/" + p["folder"] + "/" + p["file"] + ".jpg",
                "dim": p["dim"],
            })
        data.append(entry)
        idx += 1

    if start is not None or end is not None:
        data = [e for e in data if (start is None or e["i"] >= start) and (end is None or e["i"] <= end)]
        print(f"faixa: {start}..{end}")

    print("blocos:", len(data), "| total imagens:", sum(len(b["items"]) for b in data))

    # salva mapeamento blocos -> arquivos para rebuild_library.py
    out_map = [{"i": e["i"], "items": [{"folder": it["folder"], "file": it["file"]} for it in e["items"]]} for e in data]
    map_path = os.path.join(BASE, ".freebuff", "blocks_map.json")
    json.dump(out_map, open(map_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("mapeamento salvo:", map_path)

    # ---- HTML ----
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Revisao visual de pares imagem+prompt</title>
<style>
  body { background:#14161a; color:#e8e8e8; font-family:Segoe UI,Arial,sans-serif; margin:0; padding-top:64px; }
  #bar { position:fixed; top:0; left:0; right:0; background:#1e2229; padding:10px 14px; z-index:10;
         display:flex; gap:14px; align-items:center; border-bottom:1px solid #333; }
  #bar b { color:#ffd166; }
  button { cursor:pointer; border:1px solid #555; background:#2a2f38; color:#e8e8e8;
           padding:4px 10px; border-radius:6px; font-size:12px; }
  button:hover { background:#3a4150; }
  #out { position:fixed; bottom:0; left:0; right:0; height:130px; background:#0d0f12; display:none;
         padding:8px; font-size:10px; color:#9be89b; white-space:pre-wrap; overflow:auto; z-index:20; }
  .blk { border:1px solid #2c313a; border-radius:8px; margin:10px auto; padding:8px 10px; max-width:1560px; background:#191d23; }
  .btxt { color:#ffd166; font-size:12px; margin:0 0 6px 2px; line-height:1.3; }
  .bhead { display:flex; gap:10px; align-items:center; margin-bottom:6px; }
  .gdel { border-color:#a33; }
  .cells { display:grid; grid-template-columns:repeat(6, 1fr); gap:8px; }
  .cell { background:#12151a; border:1px solid #2a2f38; border-radius:6px; padding:5px; position:relative; }
  .cell img { width:100%; height:105px; object-fit:cover; border-radius:5px; background:#000; display:block; }
  .cell .lbl { font-size:9px; color:#8a94a6; margin-top:3px; }
  .cell .dim { position:absolute; top:1px; left:4px; background:rgba(0,0,0,.7); color:#9be89b; font-size:9px; padding:1px 4px; border-radius:3px; }
  .cell .x { position:absolute; top:1px; right:4px; background:#c33; color:#fff; border:none; font-size:10px; padding:1px 7px; border-radius:3px; }
  .cell.bad { border-color:#c33; }
  .cell.bad .x { background:#5a2a2a; color:#999; }
  .cell.bad img { opacity:.35; }
  .txt { font-size:10px; color:#cfd6e0; line-height:1.3; margin:4px 0 3px; max-height:40px; overflow:hidden;
         display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; }
  .multi { color:#7fd1ff; font-size:10px; }
</style>
</head>
<body>
<div id="bar">
  <span>Revisao visual — <b id="cnt">0</b> marcados invalidos</span>
  <button onclick="exp()">Exportar JSON</button>
  <button onclick="clr()">Limpar marcas</button>
  <span style="font-size:11px;color:#8a94a6">[X] = imagem NAO corresponde ao prompt / nao e um prompt valido</span>
</div>
<textarea id="out" readonly></textarea>
"""

    for b in data:
        multi = len(b["items"]) > 1
        html += f'<div class="blk" data-i="{b["i"]}">'
        if multi:
            html += f'<div class="bhead"><b class="multi">ALBUM {b["i"]} ({len(b["items"])} imagens)</b>'
            html += f'<button class="gdel" onclick="markAll({b["i"]})">X marcar TODAS invalidas</button></div>'
        html += f'<p class="btxt">{b["i"]} — {b["text"]}</p>'
        html += '<div class="cells">'
        for j, it in enumerate(b["items"]):
            html += (f'<div class="cell" id="c{b["i"]}_{j}">'
                     f'<img loading="lazy" src="{it["img"]}" alt="">'
                     f'<span class="dim">{it["dim"]}px</span>'
                     f'<button class="x" onclick="tog({b["i"]},{j})">X</button>'
                     f'<div class="lbl">{it["folder"]}/{it["file"]}</div>'
                     f'</div>')
        html += '</div></div>'

    html += """
<script>
const KEY='revmarks_v1';
let M={};
try{ M=JSON.parse(localStorage.getItem(KEY)||'{}'); }catch(e){}
function save(){ localStorage.setItem(KEY, JSON.stringify(M)); upd(); }
function upd(){ document.getElementById('cnt').textContent = Object.values(M).filter(v=>v.bad).length; }
function key(i,j){ return i+'_'+j; }
function tog(i,j){ const k=key(i,j); const el=document.getElementById('c'+k);
  if(M[k]&&M[k].bad){ delete M[k]; el.classList.remove('bad'); }
  else { M[k]={bad:true}; el.classList.add('bad'); }
  save();
}
function markAll(i){ const blk=document.querySelector('.blk[data-i="'+i+'"]');
  blk.querySelectorAll('.cell').forEach(c=>{ const p=c.id.slice(1).split('_'); const k=p[0]+'_'+p[1];
    M[k]={bad:true}; c.classList.add('bad'); });
  save();
}
function exp(){ const out=document.getElementById('out');
  out.style.display='block'; out.value=JSON.stringify(M,null,0);
  out.select(); document.execCommand('copy');
  document.title='COPIADO! '+Object.values(M).filter(v=>v.bad).length+' marcados';
}
function clr(){ if(confirm('Limpar todas as marcas?')){ M={}; localStorage.removeItem(KEY); location.reload(); } }
upd();
</script>
</body></html>
"""
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("gerado:", OUT_HTML)


if __name__ == "__main__":
    main()
