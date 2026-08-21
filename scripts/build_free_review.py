# -*- coding: utf-8 -*-
"""Gera free_review.html: revisao visual dos 100 prompts GRATUITOS do dataset.
Cada card mostra imagem + prompt completo. Botao [X] marca invalido (mismatch/people/blog).
Marcas em localStorage; export via botao (salva em .freebuff/free_marks.json)."""
import re
import json
import os

BASE = r"P:\LandingPage-PromptHub"
DS = os.path.join(BASE, "js", "prompts_dataset.js")
OUT = os.path.join(BASE, "free_review.html")

src = open(DS, encoding="utf-8").read()
data = json.loads(re.search(r"const ALL_PROMPTS_DATA = (\[.*\])\s*;?\s*$", src, re.S).group(1))
free = [d for d in data if not d["isPro"]]

cards = []
for i, d in enumerate(free):
    t = d["prompt"].replace("<", "&lt;").replace(">", "&gt;")
    cards.append(
        f'<div class="card" data-id="{d["id"]}" id="c{i}">'
        f'<div class="h"><b>{d["id"]}</b> <span class="cat">{d["cat"]}</span> '
        f'<button class="x" onclick="tog({i})">X marcar invalido</button></div>'
        f'<div class="wrap"><span class="ov">{d["id"]}</span><img loading="lazy" src="{d["img"]}"></div>'
        f'<p class="t">{t}</p></div>'
    )

html = f"""<!DOCTYPE html><html lang="pt"><head><meta charset="utf-8">
<title>Revisao FREE tier</title>
<style>
 body{{background:#0b1120;color:#eee;font-family:system-ui;margin:0;padding:8px}}
 .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}}
 .card{{border:1px solid #2a3a55;border-radius:6px;padding:4px;background:#0f1729}}
 .card.bad{{border-color:#f55;background:#2a1520}}
 .h{{display:flex;gap:6px;align-items:center;margin-bottom:4px;font-size:11px}}
 .cat{{color:#6ee7b7}}
 .x{{background:#7f1d1d;border:none;color:#fff;border-radius:3px;padding:2px 6px;cursor:pointer;margin-left:auto;font-size:10px}}
 .card.bad .x{{background:#ef4444}}
 .wrap{{position:relative}}
 .ov{{position:absolute;top:4px;left:4px;background:rgba(0,0,0,.72);color:#7ff;font-size:11px;font-weight:700;padding:1px 6px;border-radius:4px;z-index:2}}
 img{{width:100%;height:150px;object-fit:cover;border-radius:3px;display:block}}
 .t{{font-size:10px;color:#aab;max-height:36px;overflow:hidden;margin:4px 0 0;line-height:1.25}}
 .toolbar{{position:sticky;top:0;background:#0b1120;padding:6px;display:flex;gap:8px;z-index:9}}
 button{{border-radius:4px;padding:3px 8px;border:1px solid #3a4a65;background:#16233b;color:#fff;cursor:pointer}}
</style></head><body>
<div class="toolbar">
 <button onclick="exp()">EXPORTAR MARCAS</button>
 <span id="cnt"></span>
</div>
<div class="grid">{"".join(cards)}</div>
<script>
const bad = {{}};
function tog(i) {{
  const c = document.getElementById('c' + i);
  const id = c.dataset.id;
  bad[id] = !bad[id];
  c.classList.toggle('bad', bad[id]);
  document.getElementById('cnt').textContent = Object.keys(bad).filter(k => bad[k]).length + ' marcados';
}}
function exp() {{
  const out = Object.keys(bad).filter(k => bad[k]);
  localStorage.setItem('free_marks', JSON.stringify(out));
  prompt('Copie este JSON para .freebuff/free_marks.json', JSON.stringify(out));
}}
document.getElementById('cnt').textContent = '0 marcados';
</script></body></html>"""

open(OUT, "w", encoding="utf-8").write(html)
print("free_review.html gerado com", len(free), "cards ->", OUT)
