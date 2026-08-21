# -*- coding: utf-8 -*-
"""Limpeza final: remove noticias restantes (frases de reportagem), mantem prompts reais."""
import json
import re
import os

BASE = r"P:\LandingPage-PromptHub"
LIB_JS = os.path.join(BASE, "js", "prompts_library.js")
js = open(LIB_JS, encoding="utf-8").read()
data = json.loads(re.sub(r'^window.PROMPTS_LIBRARY = ', '', js).rstrip().rstrip(';'))

# frases tipicas de noticia/reportagem (nao prompt de imagem)
NEWS_FRASES = [
    r'\b(the (chinese|russian|american|ukrainian|uk|us|google|openai|anthropic|spotify|chatgpt|claude|redditor|teenager|engineer|manager|researcher|scientist|doctors|company|service|platform|device|startup|gadget))\b',
    r'\b(has (started|begun|created|released|launched|introduced|presented|announced|shown|made|learned|come up with|found|uncovered|turned|helped|reminds|invented))\b',
    r'\b(reported|article|news|official:|court refused|readers|editors|survey|study|research says|according to)\b',
    r'\b(per week|a week|salary|dollars|rubles|earns?|banned|unbanned|government)\b',
]

def is_news(t):
    p = (t or '').lower()
    hits = sum(1 for pat in NEWS_FRASES if re.search(pat, p))
    # noticia tipica tem verbo de relato + sujeito de noticia
    if hits >= 2:
        return True
    return False

filtered = [x for x in data if not is_news(x['prompt'])]
removed = len(data) - len(filtered)
open(LIB_JS, 'w', encoding='utf-8').write('window.PROMPTS_LIBRARY = %s;' % json.dumps(filtered, ensure_ascii=False))
print('removidos noticias:', removed)
print('final:', len(filtered))

from collections import Counter
print('categorias:', dict(Counter(x['categoria'] for x in filtered)))
print('por grupo:', dict(Counter(x['grupo'] for x in filtered)))