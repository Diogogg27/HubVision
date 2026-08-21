# -*- coding: utf-8 -*-
"""
Reconstrói a biblioteca completa a partir do pool coletado em PromptHub_coleta:
  100 prompts GRATUITOS (melhores textos em inglês, imagem de qualidade)
  900 prompts PREMIUM  (restante, imagem de qualidade, qualquer idioma)
Total: 1000 prompts, todos categorizados e com imagem do resultado.

Gera js/prompts_dataset.js e copia as imagens para prompts/<slug>/ (free)
e prompts/pago/<slug>/ (premium).
"""
import os
import re
import json
import hashlib
import shutil
from collections import defaultdict, Counter

from PIL import Image

BASE_DIR = r"P:\LandingPage-PromptHub"
COLETA = os.path.join(BASE_DIR, "PromptHub_coleta")
COLETA2 = os.path.join(BASE_DIR, "PromptHub_coleta_fresh")
COLETA3 = os.path.join(BASE_DIR, "PromptHub_coleta_fresh2")
FREE_DEST = os.path.join(BASE_DIR, "prompts")
PAGO_DEST = os.path.join(BASE_DIR, "prompts", "pago")
OUTPUT_JS = os.path.join(BASE_DIR, "js", "prompts_dataset.js")

FREE_TARGET = 100
PREMIUM_TARGET = 1200   # +300 premium (colecao expandida com os termos de busca)
MIN_QUALITY = 600   # menor dimensão aceitável (px)
MIN_FREE_QUALITY = 800

CATEGORY_NAMES = {
    'comida-bebida': 'Food & Drink',
    'moda-beleza': 'Fashion & Beauty',
    'produtos-publicidade': 'Products & Advertising',
    'paisagens-cidades': 'Landscapes & Cities',
    'animais': 'Animals',
    'icones-ui': 'Icons & UI',
    'objetos-arte': 'Objects & Art',
}

KEYWORDS = {
    'comida-bebida': ['food', 'drink', 'coffee', 'ice cream', 'fruit', 'burger', 'cocktail', 'dish', 'plate',
                      'breakfast', 'chocolate', 'latte', 'juice', 'gummy', 'tea', 'oil', 'marshmallow', 'martini',
                      'croissant', 'avocado', 'grapes', 'wine', 'cheese', 'cake', 'pizza', 'sushi', 'doughnut',
                      'lemon', 'orange', 'bottle of ', 'soda', 'restaurant', 'kitchen', 'edible', 'bakery',
                      'еда', 'кофе', 'десерт', 'торт', 'пицца', 'напиток'],
    'moda-beleza': ['fashion', 'dress', 'hair', 'model', 'lipstick', 'vogue', 'outfit', 'beauty', 'skin', 'jacket',
                    'balenciaga', 'portrait of a woman', 'portrait of woman', 'makeup', 'sunglasses', 'heels',
                    'accessories', 'woman', 'shirt', 'peonies', 'lingerie', 'suit', 'jewelry', 'runway', 'editorial',
                    'styl', 'модель', 'платье', 'макияж', 'прическа', 'мода', 'волос', 'девушк', 'женщин'],
    'produtos-publicidade': ['product', 'ad', 'advertising', 'rolex', 'bottle', 'package', 'mockup', 'commercial',
                             'car', 'device', 'brand', 'nike', 'diffuser', 'mercedes', 'watch', 'sculpture', 'gucci',
                             'packaging', 'poster', 'can', 'phone', 'shoes', 'sneaker', 'perfume', 'laptop',
                             'headphone', 'smartphone', 'реклам', 'товар', 'продукт', 'упаковк', 'бутылк'],
    'paisagens-cidades': ['city', 'landscape', 'desert', 'sunset', 'ocean', 'street', 'sky', 'mountain', 'beach',
                          'architecture', 'building', 'dubai', 'storm', 'lightning', 'rooftop', 'futuristic city',
                          'waterfall', 'subway', 'park', 'nature', 'forest', 'island', 'village', 'river', 'lake',
                          'snow', 'город', 'пейзаж', 'закат', 'океан', 'море', 'гор', 'пляж', 'улиц', 'небо'],
    'animais': ['cat', 'dog', 'animal', 'pet', 'kitten', 'horse', 'bird', 'lion', 'tiger', 'puppy', 'bear', 'owl',
                'rabbit', 'peeking', 'savannah', 'wildlife', 'fauna', 'duck', 'fish', 'panda', 'fox', 'wolf',
                'кот', 'собака', 'животн', 'звер', 'лис', 'волк', 'панд', 'птиц'],
    'icones-ui': ['icon', 'ui', '3d render', 'app icon', 'ios desktop icons', 'interface', 'button', 'badge',
                  'logo design', 'minimal icon', 'symbol', 'vector', 'dashboard', 'website', 'web design',
                  'иконк', 'интерфейс', 'логотип'],
    'objetos-arte': ['art', 'sculpture', 'painting', 'canvas', 'illustration', 'artwork', 'digital art', 'fanart',
                     'render', 'cinematic', 'movie', 'character', 'robot', 'cyberpunk', 'fantasy', 'portrait',
                     'neon', 'vaporwave', 'anime', 'pixel art', 'abstract', 'surreal', '3d', 'blender', 'octane',
                     'арт', 'иллюстрац', 'рисун', 'персонаж', 'кин', 'фэнтези', 'робот', 'аниме'],
}


def clean_prompt_text(text):
    if not text:
        return ""
    t = text
    # remove linhas que parecem estatisticas do telegram (numeros + tempo) / ruido
    t = re.sub(r'\d+K?\s+\d{2}:\d{2}\s*$', '', t)
    t = re.sub(r'Leave a comment.*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'Made with Inside.*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'Subscribe!.*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'Join:\s*@\S+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'Boost.*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^\s*Prompt\s*[:：]?\s*', '', t, flags=re.IGNORECASE)
    # remove hashtags, mentions e links
    t = re.sub(r'#\w+', '', t)
    t = re.sub(r'@\w+', '', t)
    t = re.sub(r'https?://\S+', '', t)
    t = re.sub(r'tg://\S+', '', t)
    # remove emojis basicos e simbolos repetidos
    lines = [re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]', '', ln).strip()
             for ln in t.split('\n')]
    lines = [ln for ln in lines if ln and not ln.startswith('✦')]
    t = ' '.join(lines)
    t = re.sub(r'\s{2,}', ' ', t)
    t = t.strip(' .,;:!-–—')
    return t[:800]


def detect_category(text):
    lower = text.lower()
    scores = {}
    for slug, words in KEYWORDS.items():
        s = sum(1 for w in words if w in lower)
        if s:
            scores[slug] = s
    if not scores:
        return 'objetos-arte'
    # desempate: maior contagem
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0]


def is_english(text):
    alpha = sum(1 for ch in text if ch.isalpha())
    if alpha == 0:
        return False
    return sum(1 for ch in text if ch.isascii() and ch.isalpha()) / alpha > 0.7


def is_spam(text):
    t = text.lower()
    if len(t) < 25:
        return True
    # sem conteudo real (so links/telegram)
    if t.count('http') >= 2 or 't.me' in t:
        return True
    if re.search(r'\d{2}:\d{2}', t) and len(t) < 80:
        return True
    return False


MOVIE_PAT = re.compile(r'\(\s*(?:19|20)\d{2}\s*\)\s*(?:Dir\.|director|реж)', re.IGNORECASE)
SPAM_PATS = [
    r"in the comments", r"our cart", r"what do you think", r"who has seen it",
    r"subscribe", r"follow", r"like and", r"share this", r"t\.me", r"boost",
    r"telegram", r"comment below", r"thoughts\?", r"opinion", r"vote",
    r"как вам", r"пишите", r"посмотрел", r"коммент", r"private feed", r"private account",
]


# ---- Criterios de aceite de par (auditoria): ----
# C4: o prompt nao pode ser descricao criada posteriormente / wrapper de canal
WRAPPER_PATS = [
    r"this prompt is perfect for", r"this prompt is fire", r"this prompt is ultra",
    r"this prompt is great", r"this banana", r"just replace", r"the result is",
    r"prompt result", r"prompt share", r"generated on", r"made with", r"in seconds",
    r"here's (a|the) (prompt|tip)", r"i (created|made) this", r"want to (see|get|create)",
    r"you can (use|try|get)", r"is the key to", r"one of the best", r"perfect for creating",
    r"incredibly powerful", r"dangerously addictive", r"killer prompt", r"ultra clean",
]
# C5: o prompt nao pode ser so referencia (foto pessoal / upload) sem prompt de geracao
REFERENCE_PATS = [
    r"upload(ed)? (your|the|a) (photo|image|picture|selfie)", r"reference image",
    r"from the uploaded", r"use the uploaded", r"attached photo", r"your photo",
    r"preserve (the )?(face|appearance)", r"keep the (face|appearance)", r"same face",
]
# C6: nao pode ser anuncio / promo / repost comercial
AD_PATS = [
    r"subscribe", r"join @", r"t\.me/", r"boost", r"promo", r"discount",
    r"buy now", r"limited offer", r"free download", r"signup", r"sign up",
    r"\$[0-9]", r"check out my", r"follow me",
]


def fails_acceptance_criteria(text):
    """True se o prompt falha nos criterios C4 (descricao-IA), C5 (referencia) ou C6 (anuncio)."""
    t = (text or "").lower()
    if any(re.search(p, t) for p in WRAPPER_PATS):
        return True
    if any(re.search(p, t) for p in REFERENCE_PATS):
        return True
    if any(re.search(p, t) for p in AD_PATS):
        return True
    return False


# Marcas da revisao visual do FREE tier: pares imagem x prompt TROCADOS (a imagem
# nao corresponde ao prompt). Bloqueio por texto distintivo — estavel entre rebuilds
# (slugs mudam a cada selecao, o texto do par nao).
MARKED_TEXTS = [
    "split-quadrant background collage divided into four equal square sections",
    "using the uploaded product as the exact reference, preserve its original shape, branding",
    "single nissan 370z (z34) wrapped in metallic rose-gold",
    "studio: food conspiracy evidence board",
    "barbie doll with a huge disheveled voluminous blonde updo",
    "two large strips of grey duct tape are placed on top of the product",
    "dense field of long green grass flowing in soft waves",
    "the avengers as kung fu panda characters",
    "extreme close-up macro shot of a young woman's eye area wearing the product",
    "seamless 4-panel product photography collage featuring the product from the uploaded image",
    "countryside landscape in the style of david hockney",
    "the cat resistance has arrived",
    "puffy icons prompt: ultra-clean 3d render of [object] in soft inflatable toy style",
    "vertical diptych collage with no gap, no border between the two images",
    "encased inside a hyper-realistic, oversized cross-section of a raspberry",
    "home alone",
    "when homer simpson enters the world of video games",
    "cinematic rear view shot of a stylish east asian couple sitting closely on a grassy field",
    "i crossed seas of sand and buried my name under a thousand storms",
    "let rivers of blood be shed in the name of the kraken",
    "shuma-gorath descends",    'a top-down pov photo of a person holding a round silver metal plate wi',
    'view from a dark shadowy hallway through an ajar antique gilded french',
    'this prompt is perfect for creating epic statue versions of your favor',
    'extreme close-up overhead shot of a dense pile of [fresh summer produc',
    'a seamless collage of two candid lifestyle photographs placed directly',
    'nano banana prompt share branded backpack concepts in minutes. try thi',
    'a cute realistic easter bunny standing upright making a peace sign wit',
    'musk: telepathy could become a reality this year elon musk said that n',
    '[product from uploaded photo] laid flat in a lush green meadow, softly',
    'surreal giant-scale product installation, a massive oversized [product',
    'gotham: blödborne...dc comics characters reimagined as if gotham city ',
    'create a photo of this person from the reference x-ray profile shot in',
    'two prompting guides for seedance 2.5. they examine the roles of refer',
    'social documentary prompt: a highly photorealistic social documentary ',
    'minimalist luxury branding mockup, top-down view of fine beige sand wi',
    'a top-down perspective of a short-haired japanese high school girl lyi',
    'fighters of the cult street fighter',
    'lifestyle product photography of [product from uploaded photo] placed ',
    'the background is solid orange with orange walls and floors. the desks',
    'minimal cinematic product shot, a white takeaway cup with lid and stra',
    'realistic scene shown from the side. show a blue table with a silver c',    'a golden fluffy pancake on a round white plate placed on a small woode',
    'studio product photo shot from behind of a person with light brown wav',
    'ultra-realistic luxury commercial product photography of a premium tra',
    'a hand holding a cardboard coffee cup carrier with two iced coffee dri',
]


def is_marked(text):
    t = (text or "").lower()
    return any(m in t for m in MARKED_TEXTS)


PERSONAL_PATS = [
    r"preserve appearance", r"maintain appearance", r"save appearance", r"keep appearance",
    r"my face", r"your face", r"face 100%", r"same face", r"keep my face", r"exact face",
    r"selfie", r"upload your (photo|selfie|image|picture)", r"upload the photo",
    r"use the uploaded photo", r"from the reference image", r"use the attached (photo|image)",
    r"facial features", r"keep (my|your) (face|features)", r"do not change (facial features|appearance|the face)",
    r"we generate", r"use upload image", r"uploaded photo as a guide",
    r"facial similarities", r"the reference image", r"preserve.*face", r"determine facial",
    r"\[person from uploaded photo\]", r"\[attached photo\]", r"facial features of",
    r"\[logo from uploaded photo\]", r"uploaded selfie", r"upload your (selfie|photo|picture|image)",
    r"officially unveiled its first", r"all-electric car", r"incredibly powerful for creating educational",
    r"stop agreeing with everything you say",
]


def is_personal_photo(text):
    """Filtra prompts de edicao de FOTO PESSOAL (selfie/upload/referencia de rosto) —
    as imagens pareadas sao fotos de pessoas reais, nao resultados de IA."""
    t = (text or "").lower()
    return any(re.search(p, t) for p in PERSONAL_PATS)


def is_bad_content(text):
    """Filtra sinopse de filme, spam de engajamento, noticias, tutoriais e promos."""
    t = (text or "").strip()
    if len(t) < 25:
        return True
    if MOVIE_PAT.search(t):
        return True
    if re.search(r"\bDir\.\s+[A-Z]", t) or re.search(r"\bDirector:\s*[A-Z]", t):
        return True
    tl = t.lower()
    if any(re.search(p, tl) for p in SPAM_PATS):
        return True
    # noticias/memes/tutoriais de IA: frases tipicas
    news_hits = 0
    for pat in [r"announced", r"launched", r"introduced", r"the company", r"startup",
                r"neural network", r"model from", r"update is", r"reported", r"million",
                r"billion", r"% of", r"according to", r"new model"]:
        if re.search(pat, tl):
            news_hits += 1
    if news_hits >= 2:
        return True
    for pat in [
        r"reasons your", r"reasons why", r"ways to", r"\d+ tips", r"\d+ reasons",
        r"is a powerful update", r"is out - and", r"new opus 4\.\d", r"opus 4\.\d",
        r"benchmarks?\s*\.?\s*what's new", r"beats competitor",
        r"how to create this in", r"step 1:.*step 2:",
        r"logo design course", r"advanced illustrator",
        r"controls the robot without", r"thinking about getting into prompt",
        r"i don't know about you, i have to go",
        r"continuity\.\s*your character changes",
        r"prompt engineering\?.*guide",
        # noticias / eventos / posts sociais (canais de design sirios e noticias de IA)
        r"\bagents-a1\b", r"35b agent", r"grok announced", r"second-best image model",
        r"syrian arab republic", r"new visual identity of", r"\bsyria\b", r"\bsyrian\b", r"\baleppo\b",
        r"google launches the search", r"be a visionary", r"i2img", r"you're missing out",
        r"script influencers", r"nano banana will be available",
        r"orshina group", r"\bflowtica\b", r"scribe - a pen", r"\$\s?30 subscription",
        r"future of work in", r"created an ai band", r"hired real musicians",
        r"collecting stamps", r"dialogue session", r"\bgelab\b", r"gui agent from microsoft",
        r"hundred days of work", r"omar dler", r"designers union",
        r"moskovsky komsomolets", r"\bshishkin\b", r"very happy with the work",
        r"photoshop shortcuts", r"how do i become a good",
        r"teach chatgpt to write", r"gone viral",
        r"masterclass", r"creative session", r"artistic event", r"my impressions from a conference",
        r"competition of glances|who will blink first",
        r"claude code quietly|classify traffic",
        r"коты дикого", r"\*\*\*\*\*",
        r"^the image (shows|depicts|displays|features)", r"^the photo (shows|depicts)",
        r"comfyui-", r"getting ready for summer with ai", r"set of hints for claude",
        r"what's the font dilemma|a phrase every designer knows",
        r"designers forum|tartous", r"colours, emblems and passion",
        r"new article in which", r"my mother's programmer|vibecoding",
        r"guide to improving your life", r"our appointment is tomorrow",
        r"microsoft began to prohibit", r"dialogue session", r"neuroslop",
        r"sold on russian marketplaces", r"ai drowns for bitcoin", r"researchers have noticed",
        r"hatcha", r"reverse captcha", r"new vision for the food served",
        r"guys from our yard", r"detects signs of",
        # spam de 'dicas de IA' (grupo RTM): posts de engajamento sem prompt
        r"ever come across a tool", r"what lesser-known tools", r"diving into photorealism",
        r"feeling lost with prompt", r"sharpening your ai skills", r"if you're looking to",
        r"want to get more from your prompts", r"settle for your first prompt",
        r"it's about creating a feedback loop", r"figuring out the right style",
        r"let's share and inspire", r"let’s share and inspire", r"share the knowledge",
        r"give it a spin across", r"brainstorm session with your ai",
        r"the economist", r"a new analysis from", r"isn't replacing creativity",
        r"flooding the world with it", r"has rolled out", r"split view with alice",
        r"personal newspaper", r"ways college students", r"seedance 2\.0",
        r"cheaper and faster than its pre", r"without delays", r"a cool neural network",
        r"developer turned", r"how to create beautiful photos",
    ]:
        if re.search(pat, tl):
            return True
    return False


def extract_real_prompt(text):
    """Extrai o prompt real de wrappers: '1-Open Gemini 2-upload 3- Paste This prompt <P>' e
    'PROMPT RESULT Title: ... Prompt Category: ... (Prompt/Actions below) Creator: ...'.
    Retorna '' quando nao ha prompt real (so metadados)."""
    if not text:
        return ""
    # tutorial wrapper (1-Open Gemini 2-upload / 1. Open ChatGPT 2. Upload / Step 1-3):
    # a imagem pareada e foto/diagrama aleatorio, nao o resultado -> junk
    if re.search(r"^\s*\d\s*[-.]\s*(?:open\s+)?(?:chatgpt|gemini)\b|step\s*\d\s*[-:]\s*(?:go to google|upload your)", text, re.I):
        return ""
    # tutorial wrapper: 3- Paste This prompt / 3. Prompt / Step 3 - Use this prompt:
    m = re.search(r"(?:3[-.]\s*(?:paste this prompt|prompt)|step\s*3\s*[-:]\s*(?:use this prompt|paste this prompt))\s*[:：]?\s*(.+)$", text, re.I)
    if m and len(m.group(1).strip()) >= 25:
        return ""  # mesmo caso: tutorial de upload -> junk
    # wrapper 'We generate ... using this prompt: <P>' / 'using these instructions:'
    m = re.search(r"using this prompt\s*[:：]?\s*(.+)$", text, re.I)
    if m and len(m.group(1).strip()) >= 25:
        return m.group(1).strip()
    m = re.search(r"using these instructions?\s*[:：]?\s*(.+)$", text, re.I)
    if m and len(m.group(1).strip()) >= 25:
        return m.group(1).strip()
    # PROMPT RESULT wrapper: pega apos o ultimo 'prompt:' real
    if re.search(r"prompt result", text, re.I):
        m = re.search(r"prompt\s*[:：]\s*(.+)$", text, re.I | re.S)
        if m:
            after = m.group(1).strip()
            if re.search(r"creator|explore more|prompt/actions|below\s*\)|upload a photo first", after, re.I) or len(after) < 25:
                return ""  # so metadados, sem prompt real
            return after
        return ""
    # limpeza de wrappers simples
    t = re.sub(r"^midjourney prompt\s*[:：]?\s*", "", text, flags=re.I)
    t = re.sub(r"^prompts?\s*\d+/\s*", "", t, flags=re.I)
    t = re.sub(r"^\d+%?\s*detailed prompt\s*(version midjourney: \d+\.\d+)?\s*prompt\s*[:：]?\s*", "", t, flags=re.I)
    t = re.sub(r"\s*миджорни бот\s*$", "", t, flags=re.I)
    t = re.sub(r"\s*midjourney bot\s*$", "", t, flags=re.I)
    return t.strip()
    return text


def load_bad_files():
    bad = set()
    p = os.path.join(BASE_DIR, ".freebuff", "bad_files.json")
    if os.path.exists(p):
        bad = set(json.load(open(p, encoding="utf-8")))
    print("arquivos invalidos:", len(bad))
    return bad


def dhash(path, size=8):
    """Perceptual hash 64-bit (dHash) para identificar a MESMA imagem em pastas diferentes."""
    im = Image.open(path).convert('L').resize((size + 1, size), Image.LANCZOS)
    px = list(im.getdata())
    bits = []
    for r in range(size):
        for c in range(size):
            bits.append(1 if px[r * (size + 1) + c] > px[r * (size + 1) + c + 1] else 0)
    return int(''.join(map(str, bits)), 2)


def popcount(x):
    return bin(x).count('1')


def load_excluded_phashes():
    """Carrega .freebuff/excluded_phashes.json: hash perceptual das imagens marcadas
    como invalidas na revisao visual (persistente entre rebuilds)."""
    p = os.path.join(BASE_DIR, ".freebuff", "excluded_phashes.json")
    if os.path.exists(p):
        data = json.load(open(p, encoding="utf-8"))
        return {int(k, 16): v for k, v in data.items()}
    return {}


def load_free_marks():
    """Carrega .freebuff/free_marks.json (slugs free invalidos revisados visualmente)
    e .freebuff/free_manifest.json (slug -> arquivo de imagem de origem no pool).
    Retorna o set de arquivos de origem a EXCLUIR do pool inteiro."""
    marks = []
    p = os.path.join(BASE_DIR, ".freebuff", "free_marks.json")
    if os.path.exists(p):
        marks = json.load(open(p, encoding="utf-8"))
    manifest = {}
    pm = os.path.join(BASE_DIR, ".freebuff", "free_manifest.json")
    if os.path.exists(pm):
        manifest = json.load(open(pm, encoding="utf-8"))
    excluded = set()
    for slug in marks:
        src = manifest.get(slug)
        if src:
            excluded.add(os.path.normpath(src))
    print("free invalidos revisados:", len(marks), "-> arquivos excluidos:", len(excluded))
    return excluded


def phash_matches(h, excluded_phashes, tol=3):
    """True se h esta a <=tol bits de algum hash excluido (mesma imagem re-compactada)."""
    for eh in excluded_phashes:
        if popcount(h ^ eh) <= tol:
            return True
    return False


def load_translated():
    """Carrega translated_pool.json: dict key=folder/file -> en text"""
    p = os.path.join(BASE_DIR, ".freebuff", "translated_pool.json")
    tmap = {}
    for item in json.load(open(p, encoding='utf-8')):
        tmap[item['folder'] + '/' + item['file']] = item.get('en', '')
    return tmap


def family_key(text):
    """Normaliza o texto para agrupar variantes quase identicas (ex: mesma pintura por artistas diferentes)."""
    t = (text or '').lower()
    t = re.sub(r"\boil impressionist painting by [a-z ]+ with a scene.*$", "oilpaint", t)
    t = re.sub(r"the background is solid orange with orange walls and floors\.?\s*", "orange office ", t)
    t = re.sub(r"\bcom casaroes antigos\b", " street ", t)
    t = re.sub(r"\b[0-9]+\b", "", t)
    t = re.sub(r"\s+", " ", t)
    return t[:60]


def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def collect_pairs(bad_files, tmap, excluded_src=None, excluded_phashes=None):
    excluded_src = excluded_src or set()
    excluded_phashes = excluded_phashes or {}
    # imagens com 2+ legendas DIFERENTES no banco de coleta = pareamento ambiguo
    # (nao ha como provar qual legenda e o prompt real da geracao) -> exclui o par
    img_texts = defaultdict(set)
    for col_dir in (COLETA, COLETA2, COLETA3):
        if not os.path.isdir(col_dir):
            continue
        for folder in os.listdir(col_dir):
            d = os.path.join(col_dir, folder)
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    continue
                base = os.path.splitext(f)[0]
                txt_p = os.path.join(d, base + '.txt')
                if not os.path.exists(txt_p):
                    continue
                img_texts[sha256_file(os.path.join(d, f))].add(
                    re.sub(r'\s+', ' ', open(txt_p, encoding='utf-8', errors='ignore').read())[:400])
    ambiguous = {h for h, ts in img_texts.items() if len(ts) >= 2}
    print("imagens com pareamento ambiguo (2+ legendas):", len(ambiguous))
    by_hash = defaultdict(list)
    for col_dir in (COLETA, COLETA2, COLETA3):
        if not os.path.isdir(col_dir):
            continue
        for folder in os.listdir(col_dir):
            d = os.path.join(col_dir, folder)
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    continue
                base = os.path.splitext(f)[0]
                txt_p = os.path.join(d, base + '.txt')
                fkey = folder + '/' + base
                if fkey in bad_files:
                    continue
                jpg = os.path.join(d, f)
                if os.path.normpath(jpg) in excluded_src:
                    continue
                if sha256_file(jpg) in ambiguous:
                    continue
                # usa texto traduzido (EN) quando disponivel
                en = tmap.get(fkey, '')
                if not en:
                    # fallback para original limpo
                    if not os.path.exists(txt_p):
                        continue
                    try:
                        en = clean_prompt_text(open(txt_p, encoding='utf-8', errors='ignore').read())
                    except Exception:
                        continue
                en = extract_real_prompt(en)
                if not en or is_spam(en) or is_personal_photo(en) or is_bad_content(en):
                    continue
                if is_marked(en):
                    continue
                if fails_acceptance_criteria(en):
                    continue
                try:
                    im = Image.open(jpg)
                    w, h = im.size
                    ph = dhash(jpg)
                except Exception:
                    w = h = 0
                    ph = None
                if ph is not None and phash_matches(ph, excluded_phashes):
                    continue
                key = hashlib.md5(en.encode('utf-8', 'ignore')).hexdigest()
                by_hash[key].append((jpg, en, max(w, h)))
    pairs = []
    for items in by_hash.values():
        best = max(items, key=lambda x: x[2])
        text = best[1]
        if not text or len(text) < 15:
            continue
        pairs.append({
            'jpg': best[0],
            'dim': best[2],
            'text': text,
            'en': is_english(text),
            'slug': detect_category(text),
            'fam': family_key(text),
        })
    # dedup por familia: mantem o melhor par por template quase identico
    by_fam = defaultdict(list)
    for p in pairs:
        by_fam[p['fam']].append(p)
    deduped = []
    for items in by_fam.values():
        if len(items) == 1:
            deduped.append(items[0])
        else:
            items.sort(key=lambda p: (-p['dim'], -len(p['text'])))
            deduped.append(items[0])
    print("dedup por familia:", len(pairs), "->", len(deduped))
    return deduped


def main():
    bad_files = load_bad_files()
    tmap = load_translated()
    excluded = load_free_marks()
    excluded_phashes = load_excluded_phashes()
    print("phashes excluidos:", len(excluded_phashes))
    pairs = collect_pairs(bad_files, tmap, excluded, excluded_phashes)
    print("pares unicos limpos:", len(pairs))
    print("distribuicao qualidade:", dict(Counter(
        ('>=1000' if p['dim'] >= 1000 else '600-999' if p['dim'] >= 600 else '300-599' if p['dim'] >= 300 else '<300')
        for p in pairs)))
    print("ingles:", sum(1 for p in pairs if p['en']))

    # ---- selecao FREE: ingles, qualidade, balanceado por categoria ----
    free_cand = [p for p in pairs if p['en'] and p['dim'] >= MIN_FREE_QUALITY]
    free_cand.sort(key=lambda p: -len(p['text']))
    free = []
    used = set()
    # balancear: rodadas por categoria (circular, ~14 por categoria)
    by_cat = defaultdict(list)
    for p in free_cand:
        by_cat[p['slug']].append(p)
    for slug in by_cat:
        by_cat[slug].sort(key=lambda p: -len(p['text']))
    slugs = list(CATEGORY_NAMES.keys())
    round_num = 0
    while len(free) < FREE_TARGET and round_num < 80:
        added = False
        for slug in slugs:
            if len(free) >= FREE_TARGET:
                break
            picked = next((p for p in by_cat.get(slug, []) if id(p) not in used), None)
            if picked:
                free.append(picked)
                used.add(id(picked))
                added = True
        if not added:
            break
        round_num += 1
    if len(free) < FREE_TARGET:
        # completa com o que houver
        for p in free_cand:
            if len(free) >= FREE_TARGET:
                break
            if id(p) not in used:
                free.append(p)
                used.add(id(p))
    print("FREE selecionados:", len(free), dict(Counter(p['slug'] for p in free)))

    # ---- selecao PREMIUM: restante com qualidade, qualquer idioma ----
    # prefere >=600px; completa ate o alvo com 300-599px
    premium_cand = [p for p in pairs if id(p) not in used and p['dim'] >= 300]
    premium_cand.sort(key=lambda p: (-(p['dim'] >= MIN_QUALITY), -p['dim'], -len(p['text'])))
    premium = premium_cand[:PREMIUM_TARGET]
    print("PREMIUM selecionados:", len(premium), dict(Counter(p['slug'] for p in premium)))

    # ---- copiar imagens ----
    free_entries = []
    for i, p in enumerate(free, start=1):
        slug = p['slug']
        dest_dir = os.path.join(FREE_DEST, slug)
        os.makedirs(dest_dir, exist_ok=True)
        name = f"free_{i:03d}.jpg"
        shutil.copy2(p['jpg'], os.path.join(dest_dir, name))
        free_entries.append({
            'cat': CATEGORY_NAMES[slug],
            'slug': slug,
            'img': f"prompts/{slug}/{name}",
            'prompt': p['text'],
            'isPro': False,
            'id': f"free_{i:03d}",
        })

    premium_entries = []
    for i, p in enumerate(premium, start=1):
        slug = p['slug']
        dest_dir = os.path.join(PAGO_DEST, slug)
        os.makedirs(dest_dir, exist_ok=True)
        name = f"premium_{i:03d}.jpg"
        shutil.copy2(p['jpg'], os.path.join(dest_dir, name))
        premium_entries.append({
            'cat': CATEGORY_NAMES[slug],
            'slug': slug,
            'img': f"prompts/pago/{slug}/{name}",
            'prompt': p['text'],
            'isPro': True,
            'id': f"premium_{i:03d}",
        })

    # manifesto slug -> arquivo de origem (para re-excluir em rebuilds futuros)
    manifest = {e['id']: p['jpg'] for e, p in zip(free_entries, free)}
    with open(os.path.join(BASE_DIR, ".freebuff", "free_manifest.json"), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print("manifesto free salvo:", len(manifest))

    all_entries = free_entries + premium_entries
    print("TOTAL:", len(all_entries))

    js_content = f"// PromptHub - Dataset completo com {len(free_entries)} Gratuitos e {len(premium_entries)} Premium\n"
    js_content += f"const ALL_PROMPTS_DATA = {json.dumps(all_entries, ensure_ascii=False, indent=2)};\n"
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("dataset gerado:", OUTPUT_JS)


if __name__ == '__main__':
    main()
