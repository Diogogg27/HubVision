# -*- coding: utf-8 -*-
"""Filtro definitivo: so mantem itens que sao prompts de imagem (ou captions visuais)."""
import json
import re
import os

BASE = r"P:\LandingPage-PromptHub"
LIB_JS = os.path.join(BASE, "js", "prompts_library.js")
js = open(LIB_JS, encoding="utf-8").read()
data = json.loads(re.sub(r'^window.PROMPTS_LIBRARY = ', '', js).rstrip().rstrip(';'))

VISUAL = r'\b(photo|photos|photograph|photography|photorealistic|image|picture|portrait|render|rendering|illustration|shot|shoot|artwork|scene|painting|drawing|sketch|cartoon|anime|manga|3d|3-d|design|icon|logo|poster|wallpaper|mockup|background|texture|model|character|landscape|cityscape|product|advertisement|advertising|campaign)\b'
PROMPT_MARK = r'(^|\s)prompt(s|ed)?[:.!]?(\s|$)|(^|\s)full prompt'
# marcadores de "instrucao de geracao" sem palavra visual explicita
GEN_INSTR = r'\b(generate|create|make|add|use the (uploaded|photo)|turn |transform|place|put|style|color|texture|lighting|composition|background|foreground|in the style of|ultra[- ]?realistic|hyper[- ]?realistic|8k|high[- ]?quality|detailed)\b'

def is_image_prompt(t):
    p = (t or '').strip().lower()
    if len(p) < 25:
        return False
    if re.search(PROMPT_MARK, p):
        return True
    if re.search(VISUAL, p):
        return True
    if re.search(GEN_INSTR, p):
        return True
    return False

# noticias que passaram no VISUAL ("photo" aparece em noticia) - bloquear por estrutura narrativa
NEWS_HARD = r'\b(the (chinese|russian|google|spotify|openai|chatgpt|claude|scientists|researchers|doctors|company|service)|user (asked|showed|redrew|created)|redditor|teenager|manager|engineer|guy|girl asked|released (a|new)|launched|introduced|reported|official:|court|article|readers|editors|startup|app (that|can|will)|device|pendant|medallion|implant|feature)\b'
# textos de promocao de canal/bot
PROMO = r'\b(go to the bot|log into the bot|attach |bot |channel (link|invite|with)|closed channel|accept orders|write in messages|prompts in the comments|for a small|more unusual prompts|follow (the|me)|subscribe|join (the|our)|@\w+)\b'

def is_junk(t):
    p = (t or '').lower()
    if re.search(PROMO, p):
        return True
    # noticia: tem NEWS_HARD E nao parece prompt de imagem
    if re.search(NEWS_HARD, p) and not is_image_prompt(p):
        return True
    if not is_image_prompt(p):
        return True
    return False

RULES = [
    ('retrato', r'\b(portrait|headshot|close[- ]?up|selfie|mugshot|face of|pretty (girl|woman)|handsome (man|boy)|human (face|portrait)|woman (with|wearing|standing|stands|in|on)|man (with|wearing|standing|stands|in|on)|girl (with|wearing|standing|stands|in|on)|boy (with|wearing|standing|in|on)|model (wearing|with)|person (in|standing|standing|wearing|with)|photo of a (woman|man|girl|boy|person))\b'),
    ('fotografia', r'\b(photograph|photography|photorealistic|photo (of|showing|with|session|shoot)|candid|35mm|film (photograph|photo)|polaroid|street photo|bokeh|macro (shot|photography|food)|editorial|lookbook|fashion (photo|photography)|still life|analog photo|telephoto|cinematic (photo|shot)|ultra-realistic photo|realistic (photo|shot)|photoshoot|photo at)\b'),
    ('publicidade', r'\b(product (photo|shot|photography|campaign)|advertisement|advertising|commercial|campaign|packaging|brand (photo|shot|campaign)|promotional|billboard|poster|luxury|cosmetics|fashion campaign|sports poster)\b'),
    ('fantasia', r'\b(fantasy|dragon|magic|magical|wizard|witch|elf|fairy|mythical|enchanted|medieval|knight|potion|mage|demon|vampire|sorcerer|spell|royal (queen|king|princess)|mythology|goddess)\b'),
    ('ficcao cientifica', r'\b(sci[- ]?fi|cyberpunk|futuristic|robot|android|spaceship|space (station|ship|craft)|alien|dystopian|hologram|mecha|nanotech|neon (city|lights)|ai android|cyborg|technology)\b'),
    ('arquitetura', r'\b(architecture|architectural|building|skyscraper|facade|interior|modern (house|villa|interior|building)|minimalist|exterior (of|shot)|real estate|room|hallway|apartment|living room|kitchen|office (interior|space)|cafe|restaurant|architect)\b'),
    ('anime', r'\b(anime|manga|japanese (style|art|animation)|chibi|studio ghibli|shonen|sakura|cosplay|kawaii|waifu)\b'),
    ('3d', r'\b(3d|3-d|pixar|blender|octane render|cgi|unreal engine|cinema 4d|zbrush|vray|low[- ]?poly|isometric|voxel|3d render|animated (style|film)|cartoon (style|character)|toy (render|style))\b'),
    ('paisagem', r'\b(landscape|mountain|ocean|beach|sunset|sunrise|forest|waterfall|river|lake|field (of|with)|aurora|night sky|starry|snowy|desert|cliff|canyon|skyline|cityscape|scenic|nature|outdoor|seaside|sea shore|on the (sea|beach))\b'),
    ('arte conceitual', r'\b(concept art|matte painting|digital (art|illustration)|artstation|character (design|art|sheet)|key art|illustration|sketch|painting|watercolor|oil painting|brush stroke|drawing|abstract|graphic|minimal)\b'),
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
    if is_junk(x['prompt']):
        removed += 1
        continue
    x['categoria'] = categorize(x['prompt'])
    filtered.append(x)

open(LIB_JS, 'w', encoding='utf-8').write('window.PROMPTS_LIBRARY = %s;' % json.dumps(filtered, ensure_ascii=False))
print('removidos:', removed)
print('final:', len(filtered))
print('categorias:', dict(Counter(x['categoria'] for x in filtered)))