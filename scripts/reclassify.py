# -*- coding: utf-8 -*-
"""
Reclassifica categorias do dataset prompts_library.js com regras mais amplas.
"""
import json
import re
import os

BASE = r"P:\LandingPage-PromptHub"
LIB_JS = os.path.join(BASE, "js", "prompts_library.js")

js = open(LIB_JS, encoding="utf-8").read()
data = json.loads(re.sub(r'^window.PROMPTS_LIBRARY = ', '', js).rstrip().rstrip(';'))

RULES = [
    ('retrato', r'\b(portrait|headshot|close[- ]?up of a (man|woman|girl|boy|person|face)|selfie|mugshot|face of|pretty (girl|woman)|handsome (man|boy))\b'),
    ('fotografia', r'\b(photograph|photo (of|showing|with)|photorealistic|candid|35mm|film photograph|polaroid|street photography|bokeh|macro shot|editorial photo|lookbook)\b'),
    ('publicidade', r'\b(product (photo|shot|photography)|advertisement|advertising|commercial|packaging|brand (photo|shot)|promotional|billboard|poster ad)\b'),
    ('fantasia', r'\b(fantasy|dragon|magic|wizard|witch|elf|fairy|mythical|enchanted|medieval castle|knight|potion|mage|demon|vampire)\b'),
    ('ficcao cientifica', r'\b(sci[- ]?fi|cyberpunk|futuristic|robot|android|spaceship|space (station|ship)|alien|dystopian|hologram|mecha|nanotech|neon city|ai android)\b'),
    ('arquitetura', r'\b(architecture|architectural|building|skyscraper|facade|interior (design|shot|of a)|modern (house|villa)|minimalist (interior|architecture)|exterior of|real estate)\b'),
    ('anime', r'\b(anime|manga|japanese (style|art)|chibi|studio ghibli|shonen|sakura|cosplay art)\b'),
    ('3d', r'\b(3d|3-d|pixar|blender|render|octane|cgi|unreal engine|cinema 4d|zbrush|vray|low[- ]?poly|isometric (render|view)|voxel)\b'),
    ('paisagem', r'\b(landscape|mountain|ocean|beach|sunset|sunrise|forest|waterfall|river|lake|field of|aurora|night sky|starry|snowy|desert|cliff|canyon)\b'),
    ('arte conceitual', r'\b(concept art|conceptart|matte painting|digital art|artstation|character (design|art|sheet)|key art|illustration by|fantasy (concept|illustration))\b'),
]

def categorize(t):
    p = (t or '').lower()
    for cat, pat in RULES:
        if re.search(pat, p):
            return cat
    return 'outros'

from collections import Counter
new_cats = Counter()
for x in data:
    c = categorize(x['prompt'])
    x['categoria'] = c
    new_cats[c] += 1

open(LIB_JS, 'w', encoding='utf-8').write('window.PROMPTS_LIBRARY = %s;' % json.dumps(data, ensure_ascii=False))
print('novas categorias:', dict(new_cats))