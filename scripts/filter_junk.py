# -*- coding: utf-8 -*-
"""Remove lixo (nao-prompts) e reclassifica fotos genericas."""
import json
import re
import os

BASE = r"P:\LandingPage-PromptHub"
LIB_JS = os.path.join(BASE, "js", "prompts_library.js")
js = open(LIB_JS, encoding="utf-8").read()
data = json.loads(re.sub(r'^window.PROMPTS_LIBRARY = ', '', js).rstrip().rstrip(';'))

JUNK_PAT = r'\b(prompts? in the comments|prompts? (at|on) the comments|accept orders|write in messages|closed channel|more unusual prompts|subscribe|follow (the|for)|join (the|our)|comments( for|:)?|leave a comment|like and|share this|channel (link|invite)|telegram|@\w+|donate|support me|dm me|contact me|for orders|price|cheap|buy|sell)\b'

def is_junk_prompt(t):
    p = (t or '').lower()
    if re.search(r'\b(prompts in the comments|accept orders|write in messages|more unusual prompts|closed channel|i accept orders)\b', p):
        return True
    if len(p) < 40:
        return True
    # noticias / nao-imagem: sem palavras visuais de imagem
    if re.search(r'\b(the editors|readers|article|news|report|announcement|update on|launched|introduced|released (a|new)|now available|you can now|weekly|monthly)\b', p):
        if not re.search(r'\b(photo|image|prompt|render|illustration|picture|shot)\b', p):
            return True
    return False

RULES = [
    ('retrato', r'\b(portrait|headshot|close[- ]?up|selfie|mugshot|face of|pretty (girl|woman)|handsome (man|boy)|human (face|portrait)|woman (with|wearing|standing|in|on)|man (with|wearing|standing|in|on)|girl (with|wearing|standing|in)|boy (with|wearing|standing|in)|model (wearing|with))\b'),
    ('fotografia', r'\b(photograph|photography|photorealistic|photo (of|showing|with|session|shoot)|candid|35mm|film (photograph|photo)|polaroid|street photo|bokeh|macro (shot|photography|food)|editorial|lookbook|fashion (photo|photography)|still life|analog photo|telephoto|cinematic (photo|shot)|ultra-realistic photo|realistic (photo|shot))\b'),
    ('publicidade', r'\b(product (photo|shot|photography|campaign)|advertisement|advertising|commercial|campaign|packaging|brand (photo|shot|campaign)|promotional|billboard|poster|luxury|cosmetics|fashion campaign|sports poster)\b'),
    ('fantasia', r'\b(fantasy|dragon|magic|magical|wizard|witch|elf|fairy|mythical|enchanted|medieval|knight|potion|mage|demon|vampire|sorcerer|spell|royal (queen|king|princess))\b'),
    ('ficcao cientifica', r'\b(sci[- ]?fi|cyberpunk|futuristic|robot|android|spaceship|space (station|ship|craft)|alien|dystopian|hologram|mecha|nanotech|neon (city|lights)|ai android|cyborg|tech)\b'),
    ('arquitetura', r'\b(architecture|architectural|building|skyscraper|facade|interior|modern (house|villa|interior|building)|minimalist|exterior (of|shot)|real estate|room|hallway|apartment|living room|kitchen|office (interior|space)|cafe|restaurant interior)\b'),
    ('anime', r'\b(anime|manga|japanese (style|art|animation)|chibi|studio ghibli|shonen|sakura|cosplay|kawaii|waifu)\b'),
    ('3d', r'\b(3d|3-d|pixar|blender|octane render|cgi|unreal engine|cinema 4d|zbrush|vray|low[- ]?poly|isometric|voxel|3d render|animated (style|film)|cartoon (style|character)|toy (render|style))\b'),
    ('paisagem', r'\b(landscape|mountain|ocean|beach|sunset|sunrise|forest|waterfall|river|lake|field (of|with)|aurora|night sky|starry|snowy|desert|cliff|canyon|skyline|cityscape|scenic|nature|outdoor)\b'),
    ('arte conceitual', r'\b(concept art|matte painting|digital (art|illustration)|artstation|character (design|art|sheet)|key art|illustration|sketch|painting|watercolor|oil painting|brush stroke|drawing|abstract)\b'),
]

def categorize(t):
    p = (t or '').lower()
    for cat, pat in RULES:
        if re.search(pat, p):
            return cat
    return 'outros'

from collections import Counter
filtered = []
removed = 0
for x in data:
    if is_junk_prompt(x['prompt']):
        removed += 1
        continue
    x['categoria'] = categorize(x['prompt'])
    filtered.append(x)

open(LIB_JS, 'w', encoding='utf-8').write('window.PROMPTS_LIBRARY = %s;' % json.dumps(filtered, ensure_ascii=False))
print('removidos junk:', removed)
print('final:', len(filtered))
print('categorias:', dict(Counter(x['categoria'] for x in filtered)))