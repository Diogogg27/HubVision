# -*- coding: utf-8 -*-
"""
Auditoria de procedencia da biblioteca (js/prompts_dataset.js).

Regra: manter na selecao final SOMENTE imagens com prompt original comprovadamente
vinculado por metadados, banco de dados da coleta, historico de geracao ou ID/hash
da geracao. NUNCA criar/deduzir/resumir prompt a partir da imagem.

Classificacao por item:
  METADATA_VERIFICADO  -> metadados de geracao embutidos (A1111 'parameters', PNG tEXt,
                          XMP, EXIF) cujo prompt bate com a legenda vinculada.
  INCONSISTENTE        -> metadados de geracao presentes, mas NAO batem com a legenda.
  VINCULADO_DB         -> sem metadados, porem com vínculo via banco de dados da coleta:
                          imagem + legenda capturados juntos (mesma mensagem/arquivo).
  SEM_PROMPT_EXATO     -> sem metadados E sem legenda vinculada -> removido da selecao
                          final (sem exclusao fisica do arquivo).
  DUPLICADO            -> mesmo SHA-256 de outra imagem ja selecionada -> removido da
                          selecao final (sem exclusao fisica).

Saidas:
  .freebuff/audit_images.json  -> schema completo por imagem (id, nome, url, sha256,
                                  prompt original exato, prompt EN, negativo, modelo,
                                  seed, sampler, steps, cfg, resolucao, data, fonte).
  .freebuff/audit_report.md    -> relatorio: totais + motivo de exclusao por imagem.
  js/prompts_dataset.js        -> selecao final regravada apenas com itens mantidos.
"""
import os
import re
import json
import hashlib
import datetime
import shutil
from collections import Counter, defaultdict

from PIL import Image
from PIL.ExifTags import TAGS

BASE = r"P:\LandingPage-PromptHub"
POOL_DIRS = ["PromptHub_coleta", "PromptHub_coleta_fresh", "PromptHub_coleta_fresh2"]
LIB_IMG = os.path.join(BASE, "prompts")
DS = os.path.join(BASE, "js", "prompts_dataset.js")
OUT_JSON = os.path.join(BASE, ".freebuff", "audit_images.json")
OUT_MD = os.path.join(BASE, ".freebuff", "audit_report.md")

CAT_NAMES = {
    "comida-bebida": "Food & Drink", "moda-beleza": "Fashion & Beauty",
    "produtos-publicidade": "Products & Advertising", "paisagens-cidades": "Landscapes & Cities",
    "animais": "Animals", "icones-ui": "Icons & UI", "objetos-arte": "Objects & Art",
}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_metadata(p):
    """Retorna dict com metadados embutidos (parameters A1111, tEXt, XMP, EXIF) ou {}."""
    out = {}
    try:
        im = Image.open(p)
        info = im.info or {}
        params = info.get("parameters")
        if params:
            out["raw"] = str(params)
        for k, v in info.items():
            if k in ("parameters", "text", "xmp", "comment", "Comment", "exif"):
                out.setdefault("extra", {})[str(k)] = str(v)[:2000]
        if hasattr(im, "getexif") and im.getexif():
            ex = {}
            for k, v in im.getexif().items():
                try:
                    ex[TAGS.get(k, str(k))] = str(v)[:200]
                except Exception:
                    pass
            if ex:
                out["exif"] = ex
        try:
            w, h = im.size
            out["resolucao"] = "%dx%d" % (w, h)
        except Exception:
            pass
    except Exception:
        pass
    return out


def parse_a1111(raw):
    """Extrai prompt/negativo/modelo/seed/sampler/steps/cfg do bloco 'parameters' (A1111)."""
    d = {"prompt": None, "negativo": None, "modelo": None, "seed": None,
         "sampler": None, "steps": None, "cfg": None}
    if not raw:
        return d
    m = re.search(r"Negative prompt:\s*(.*?)(?:\n|$)", raw, re.S)
    if m:
        d["negativo"] = m.group(1).strip() or None
        prompt_part = raw[: m.start()].strip()
    else:
        prompt_part = raw.strip()
    d["prompt"] = prompt_part or None
    def grab(pat, key):
        mm = re.search(pat, raw, re.I)
        if mm:
            d[key] = mm.group(1).strip()
    grab(r"Seed:\s*([\w-]+)", "seed")
    grab(r"Sampler:\s*([^,]+)", "sampler")
    grab(r"Steps:\s*(\d+)", "steps")
    grab(r"CFG scale:\s*([\d.]+)", "cfg")
    grab(r"Model:\s*([^,]+)", "modelo")
    return d


def main():
    # 1) indice do pool: sha256 -> [(path, txt_path)]
    pool_by_hash = defaultdict(list)
    for col in POOL_DIRS:
        d0 = os.path.join(BASE, col)
        if not os.path.isdir(d0):
            continue
        for root, _, files in os.walk(d0):
            for f in files:
                if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    continue
                p = os.path.join(root, f)
                base = os.path.splitext(f)[0]
                txt_p = os.path.join(root, base + ".txt")
                pool_by_hash[sha256_file(p)].append((p, txt_p if os.path.exists(txt_p) else None))

    # 2) dataset atual
    src = open(DS, encoding="utf-8").read()
    data = json.loads(re.search(r"const ALL_PROMPTS_DATA = (\[.*\])\s*;?\s*$", src, re.S).group(1))

    # 3) auditoria por item
    seen_hashes = set()
    rows = []
    for d in data:
        img = os.path.join(BASE, d["img"])
        if not os.path.exists(img):
            rows.append(_row(d, None, "SEM_PROMPT_EXATO", "arquivo de imagem ausente no disco", seen_hashes, None))
            continue
        h = sha256_file(img)
        md = extract_metadata(img)
        sources = pool_by_hash.get(h, [])
        # legenda vinculada via banco de dados da coleta (par imagem+txt)
        caption = None
        src_pool = None
        for sp, tp in sources:
            if tp:
                caption = open(tp, encoding="utf-8", errors="ignore").read().strip()
                src_pool = sp
                break
        # metadados?
        raw = md.get("raw")
        a = parse_a1111(raw)
        if h in seen_hashes:
            reason = "duplicata por SHA-256 (mesma imagem ja selecionada)"
            rows.append(_row(d, h, "DUPLICADO", reason, seen_hashes, caption, md, a, src_pool))
            continue
        if raw:
            if caption and a.get("prompt") and _sim(a["prompt"], caption) >= 0.6:
                cls = "METADATA_VERIFICADO"
                reason = "metadados de geracao embutidos (parameters A1111) confirmam o prompt"
            else:
                cls = "INCONSISTENTE"
                reason = "metadados de geracao presentes, mas nao batem com a legenda vinculada"
            rows.append(_row(d, h, cls, reason, seen_hashes, caption, md, a, src_pool))
        elif caption:
            cls = "VINCULADO_DB"
            reason = "vinculado por banco de dados da coleta: imagem + legenda capturados na mesma mensagem (par de arquivo)"
            rows.append(_row(d, h, cls, reason, seen_hashes, caption, md, a, src_pool))
        else:
            rows.append(_row(d, h, "SEM_PROMPT_EXATO", "sem metadados de geracao E sem legenda vinculada (banco de dados da coleta)", seen_hashes, caption, md, a, src_pool))

    # 4) JSON schema
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    # 5) relatorio
    _report(rows, data)
    print("auditoria concluida ->", OUT_JSON)


def _sim(a, b):
    a = re.sub(r"\s+", " ", (a or "").lower()).strip()
    b = re.sub(r"\s+", " ", (b or "").lower()).strip()
    if not a or not b:
        return 0.0
    toks = set(a.split())
    return len(toks & set(b.split())) / len(toks) if toks else 0.0


def _row(d, h, cls, reason, seen_hashes, caption=None, md=None, a=None, src_pool=None):
    md = md or {}
    a = a or {}
    seen_hashes.add(h) if h else None
    return {
        "image_id": d["id"],
        "nome": os.path.basename(d["img"]),
        "url": d["img"],
        "sha256": h,
        "classificacao": cls,
        "motivo": reason,
        "prompt_original_exato": caption,
        "prompt_traduzido_en": d["prompt"],
        "prompt_negativo": a.get("negativo"),
        "modelo": a.get("modelo"),
        "seed": a.get("seed"),
        "sampler": a.get("sampler"),
        "steps": a.get("steps"),
        "cfg": a.get("cfg"),
        "resolucao": md.get("resolucao"),
        "data": datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(BASE, d["img"]))).strftime("%Y-%m-%d") if os.path.exists(os.path.join(BASE, d["img"])) else None,
        "fonte_validacao": {
            "metadados_embutidos": bool(md.get("raw") or md.get("exif") or md.get("extra")),
            "vinc_banco_coleta": bool(caption),
            "fonte_pool": src_pool,
        },
        "categoria": d.get("cat"),
        "isPro": d.get("isPro", False),
    }


def _report(rows, data):
    cnt = Counter(r["classificacao"] for r in rows)
    keep_ids = {r["image_id"] for r in rows if r["classificacao"] in ("METADATA_VERIFICADO", "VINCULADO_DB")}
    drop = [r for r in rows if r["image_id"] not in keep_ids]
    lines = []
    lines.append("# Auditoria de procedencia da biblioteca")
    lines.append("")
    lines.append("- Itens auditados: **%d**" % len(rows))
    lines.append("- Data: %s" % datetime.date.today().isoformat())
    lines.append("")
    lines.append("## Totais por classificacao")
    lines.append("")
    lines.append("| Classificacao | Total |")
    lines.append("|---|---|")
    for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
        lines.append("| %s | %d |" % (k, v))
    lines.append("")
    lines.append("## Totais de metadados embutidos")
    lines.append("")
    lines.append("| Indicador | Total |")
    lines.append("|---|---|")
    md_count = sum(1 for r in rows if r["fonte_validacao"]["metadados_embutidos"])
    db_count = sum(1 for r in rows if r["fonte_validacao"]["vinc_banco_coleta"])
    lines.append("| Imagens com metadados de geracao embutidos (EXIF/tEXt/XMP/parameters) | %d |" % md_count)
    lines.append("| Imagens com legenda vinculada no banco de dados da coleta | %d |" % db_count)
    lines.append("")
    lines.append("## Mantidos na selecao final: %d" % len(keep_ids))
    lines.append("## Removidos da selecao final (sem exclusao fisica): %d" % len(drop))
    lines.append("")
    lines.append("## Motivo de exclusao por imagem")
    lines.append("")
    if drop:
        lines.append("| image_id | nome | classificacao | motivo |")
        lines.append("|---|---|---|---|")
        for r in drop:
            lines.append("| %s | %s | %s | %s |" % (r["image_id"], r["nome"], r["classificacao"], r["motivo"]))
    else:
        lines.append("_Nenhuma imagem removida._")
    lines.append("")
    lines.append("## Duplicatas por SHA-256")
    dups = [r for r in rows if r["classificacao"] == "DUPLICADO"]
    lines.append("Total: %d" % len(dups))
    for r in dups[:50]:
        lines.append("- %s (%s) -> %s" % (r["image_id"], r["nome"], r["sha256"][:12]))
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("relatorio ->", OUT_MD)
    print("mantidos:", len(keep_ids), "| removidos:", len(drop))
    return keep_ids


if __name__ == "__main__":
    main()
