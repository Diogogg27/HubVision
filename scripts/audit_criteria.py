# -*- coding: utf-8 -*-
"""
Auditoria da biblioteca contra os 8 criterios de aceite de par (prompt+imagem).

Criterios:
  C1 imagem visualizavel            -> arquivo existe + decodifica + dimensoes > 0
  C2 prompt textual associado       -> legenda vinculada na mesma publicacao (banco de coleta)
  C3 relacao comprovavel            -> vínculo por banco de dados da coleta (mesma mensagem)
  C4 prompt nao e descricao-IA      -> sem wrappers/meta ("this prompt is perfect for",
                                       "just replace", "prompt result", "share:", etc.)
  C5 nao e so imagem de referencia  -> sem marcadores de foto/referencia/upload
  C6 nao e anuncio/repost/dup       -> sem marcadores promocionais; nao-duplicata SHA-256
  C7 prompt preservado integralmente-> original completo registrado no JSON de auditoria
  C8 origem registrada              -> caminho de origem no pool registrado

Saidas:
  .freebuff/audit_criteria.json     -> por item: criterios + evidencias
  .freebuff/audit_report.md         -> secoes de criterios adicionadas
"""
import os
import re
import json
import hashlib
from collections import Counter

from PIL import Image

BASE = r"P:\LandingPage-PromptHub"
DS = os.path.join(BASE, "js", "prompts_dataset.js")
AUDIT = os.path.join(BASE, ".freebuff", "audit_images.json")
OUT = os.path.join(BASE, ".freebuff", "audit_criteria.json")
REPORT = os.path.join(BASE, ".freebuff", "audit_report.md")

# marcadores de "descricao criada por IA depois" / wrapper de canal
WRAPPER_PATS = [
    r"this prompt is perfect for", r"this prompt is fire", r"this prompt is ultra",
    r"this prompt is great", r"this banana", r"just replace", r"the result is",
    r"the results? (are|look)", r"prompt result", r"prompt share", r"share:",
    r"generated on", r"made with", r"in seconds", r"here's (a|the) (prompt|tip)",
    r"i (created|made) this", r"check out", r"want to (see|get|create)",
    r"you can (use|try|get)", r"is the key to", r"one of the best", r"perfect for creating",
    r"incredibly powerful", r"dangerously addictive", r"killer prompt", r"ultra clean",
]
REFERENCE_PATS = [
    r"upload(ed)? (your|the|a) (photo|image|picture|selfie)", r"reference image",
    r"from the uploaded", r"use the uploaded", r"attached photo", r"your photo",
    r"preserve (the )?(face|appearance)", r"keep the (face|appearance)", r"same face",
]
AD_PATS = [
    r"subscribe", r"join @", r"t\.me/", r"telegram", r"boost", r"promo", r"discount",
    r"buy now", r"limited offer", r"free download", r"signup", r"sign up",
    r"\$[0-9]", r"check out my", r"follow me",
]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def main():
    src = open(DS, encoding="utf-8").read()
    data = json.loads(re.search(r"const ALL_PROMPTS_DATA = (\[.*\])\s*;?\s*$", src, re.S).group(1))
    audit = {r["image_id"]: r for r in json.load(open(AUDIT, encoding="utf-8"))}

    seen = set()
    rows = []
    for d in data:
        img = os.path.join(BASE, d["img"])
        a = audit.get(d["id"], {})
        cr = {}
        # C1 imagem visualizavel
        c1 = False
        try:
            im = Image.open(img)
            im.load()
            w, h = im.size
            c1 = (w > 0 and h > 0)
        except Exception:
            c1 = False
        cr["C1_imagem_visualizavel"] = {"pass": c1, "evidencia": "%dx%d" % (w, h) if c1 else "arquivo invalido"}
        # C2 prompt associado (banco de coleta)
        c2 = bool(a.get("fonte_validacao", {}).get("vinc_banco_coleta") or a.get("prompt_original_exato"))
        cr["C2_prompt_associado"] = {"pass": c2, "evidencia": "legenda vinculada na mesma publicacao (par de arquivo no pool)" if c2 else "sem legenda"}
        # C3 relacao comprovavel (banco de dados da coleta)
        c3 = bool(a.get("fonte_validacao", {}).get("fonte_pool")) and c2
        cr["C3_relacao_comprovavel"] = {"pass": c3, "evidencia": "mesma mensagem capturada (fonte: %s)" % os.path.basename(os.path.dirname(a.get("fonte_validacao", {}).get("fonte_pool") or "?")) if c3 else "sem registro de origem"}
        # C4 nao-descricao-IA
        t = (d.get("prompt") or "").lower()
        hits = [p for p in WRAPPER_PATS if re.search(p, t)]
        c4 = len(hits) == 0
        cr["C4_nao_descricao_ia"] = {"pass": c4, "evidencia": "sem marcadores de wrapper" if c4 else "marcadores: %s" % ", ".join(hits[:3])}
        # C5 nao-referencia
        rhits = [p for p in REFERENCE_PATS if re.search(p, t)]
        c5 = len(rhits) == 0
        cr["C5_nao_referencia"] = {"pass": c5, "evidencia": "sem marcadores de foto de referencia" if c5 else "marcadores: %s" % ", ".join(rhits[:3])}
        # C6 nao-anuncio/duplicado
        ahits = [p for p in AD_PATS if re.search(p, t)]
        h = sha256_file(img) if os.path.exists(img) else None
        dup = h in seen
        seen.add(h)
        c6 = len(ahits) == 0 and not dup
        cr["C6_nao_anuncio_repost"] = {"pass": c6, "evidencia": "sem marcadores promocionais e sem duplicata SHA-256" if c6 else ("anuncio: %s" % ", ".join(ahits[:2]) if ahits else "duplicata SHA-256")}
        # C7 prompt integral
        c7 = bool(a.get("prompt_original_exato"))
        cr["C7_prompt_integral"] = {"pass": c7, "evidencia": "original completo registrado no JSON de auditoria" if c7 else "original nao registrado"}
        # C8 origem registrada
        c8 = bool(a.get("fonte_validacao", {}).get("fonte_pool"))
        cr["C8_origem_registrada"] = {"pass": c8, "evidencia": a.get("fonte_validacao", {}).get("fonte_pool") or "sem origem"}
        ok = all(v["pass"] for v in cr.values())
        rows.append({"image_id": d["id"], "categoria": d.get("cat"), "isPro": d.get("isPro", False),
                     "aprovado": ok, "criterios": cr})

    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # relatorio
    n_ok = sum(1 for r in rows if r["aprovado"])
    n_fail = len(rows) - n_ok
    c_cnt = Counter()
    for r in rows:
        for k, v in r["criterios"].items():
            if not v["pass"]:
                c_cnt[k] += 1
    fails = [r for r in rows if not r["aprovado"]]
    md = []
    md.append("\n## Auditoria de criterios de aceite (8 criterios)")
    md.append("")
    md.append("- Itens auditados: **%d**" % len(rows))
    md.append("- Aprovados em todos os criterios: **%d**" % n_ok)
    md.append("- Reprovados (>=1 criterio): **%d**" % n_fail)
    md.append("")
    md.append("| Criterio | Reprovacoes |")
    md.append("|---|---|")
    for k, v in sorted(c_cnt.items(), key=lambda kv: -kv[1]):
        md.append("| %s | %d |" % (k, v))
    md.append("")
    md.append("### Itens reprovados")
    md.append("")
    md.append("| image_id | categoria | motivo |")
    md.append("|---|---|---|")
    for r in fails:
        motivos = [k + "(" + v["evidencia"][:40] + ")" for k, v in r["criterios"].items() if not v["pass"]]
        md.append("| %s | %s | %s |" % (r["image_id"], r["categoria"], "; ".join(motivos)))
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("criterios: aprovados=%d reprovados=%d" % (n_ok, n_fail))
    print("reprovacoes por criterio:", dict(c_cnt))


if __name__ == "__main__":
    main()
