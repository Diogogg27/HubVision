# -*- coding: utf-8 -*-
"""Reclassifica com regras mais amplas."""
import json
import re
import os

BASE = r"P:\LandingPage-PromptHub"
LIB_JS = os.path.join(BASE, "js", "prompts_library.js")
js = open(LIB_JS, encoding="utf-8").read()
data = json.loads(re.sub(r'^window.PROMPTS_LIBRARY = ', '', js).rstrip().rstrip(';'))

RULES = [
    ('retrato', r'\b(portrait|headshot|close[- ]?up (of|shot) (a )?(man|woman|girl|boy|person|face)|selfie|mugshot|face of|pretty (girl|woman)|handsome (man|boy)|human (face|portrait)|woman (with|wearing|standing)|man (with|wearing|standing))\b'),
    ('fotografia', r'\b(photograph|photography|photorealistic|photo (of|showing|with|session|shoot)|candid|35mm|film (photograph|photo)|polaroid|street photo|bokeh|macro (shot|photography|food)|editorial photo|lookbook|fashion photo|still life|aperture|shutter|35 mm|analog photo)\b'),
    ('publicidade', r'\b(product (photo|shot|photography|campaign)|advertisement|advertising|commercial|campaign (photo|shot)|packaging|brand (photo|shot|campaign)|promotional|billboard|poster (ad|design)|luxury (brand|fragrance|watch)|cosmetics|fashion campaign)\b'),
    ('fantasia', r'\b(fantasy|dragon|magic|magical|wizard|witch|elf|fairy|mythical|enchanted|medieval|knight|potion|mage|demon|vampire|sorcerer|spell|enchanted|royal (queen|king|princess))\b'),
    ('ficcao cientifica', r'\b(sci[- ]?fi|cyberpunk|futuristic|futurist|robot|android|spaceship|space (station|ship|craft)|alien|dystopian|hologram|mecha|nanotech|neon (city|lights)|ai android|cyborg|technology (device|gadget))\b'),
    ('arquitetura', r'\b(architecture|architectural|building|skyscraper|facade|interior (design|shot|of a|view)|modern (house|villa|interior|building)|minimalist (interior|architecture)|exterior (of|shot)|real estate|room|hallway|apartment|living room|kitchen|office (interior|space))\b'),
    ('anime', r'\b(anime|manga|japanese (style|art|animation)|chibi|studio ghibli|shonen|sakura|cosplay|kawaii|waifu|aesthetic anime)\b'),
    ('3d', r'\b(3d|3-d|pixar|blender|octane render|cgi|unreal engine|cinema 4d|zbrush|vray|low[- ]?poly|isometric|voxel|3d render|render (of|style)|animated (style|film)|cartoon (style|character)|toy (render|style))\b'),
    ('paisagem', r'\b(landscape|mountain|ocean|beach|sunset|sunrise|forest|waterfall|river|lake|field (of|with)|aurora|night sky|starry|snowy|desert|cliff|canyon|skyline|cityscape|scenic|nature)\b'),
    ('arte conceitual', r'\b(concept art|matte painting|digital (art|illustration)|artstation|character (design|art|sheet)|key art|illustration|sketch|painting|watercolor|oil painting|brush stroke|drawing)\b'),
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
    x['categoria'] = categorize(x['prompt'])
    new_cats[x['categoria']] += 1

open(LIB_JS, 'w', encoding='utf-8').write('window.PROMPTS_LIBRARY = %s;' % json.dumps(data, ensure_ascii=False))
print('categorias:', dict(new_cats))