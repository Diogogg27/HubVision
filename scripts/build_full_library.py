import os
import re
import json
import random

BASE_DIR = r"p:\LandingPage-PromptHub"
BAK_FILE = os.path.join(BASE_DIR, "js", "main.js.bak")
TELEGRAM_DATA = os.path.join(BASE_DIR, "js", "telegram_coleta_data.json")
OUTPUT_JS = os.path.join(BASE_DIR, "js", "prompts_dataset.js")

CATEGORY_SLUGS = {
    'Comida & Bebida': 'comida-bebida',
    'Moda & Beleza': 'moda-beleza',
    'Produtos & Publicidade': 'produtos-publicidade',
    'Paisagens & Cidades': 'paisagens-cidades',
    'Animais': 'animais',
    'Icones & UI': 'icones-ui',
    'Objetos & Arte': 'objetos-arte'
}

CATEGORIES = [
    {"name": "Comida & Bebida", "slug": "comida-bebida"},
    {"name": "Moda & Beleza", "slug": "moda-beleza"},
    {"name": "Produtos & Publicidade", "slug": "produtos-publicidade"},
    {"name": "Paisagens & Cidades", "slug": "paisagens-cidades"},
    {"name": "Animais", "slug": "animais"},
    {"name": "Icones & UI", "slug": "icones-ui"},
    {"name": "Objetos & Arte", "slug": "objetos-arte"}
]

PROMPT_TEMPLATES = [
    ("Midjourney v7", "Hyper-realistic commercial studio photography of {subject}, illuminated by soft directional rim light, high resolution 8k, cinematic color grading, shallow depth of field --ar 16:9 --v 7.0 --stylize 250"),
    ("DALL-E 3", "An ultra-detailed 8K portrait of {subject}, vibrant harmonious color scheme, soft ambient glow, shot on 85mm f/1.4 lens, elegant composition, award-winning lighting."),
    ("Stable Diffusion XL", "Masterpiece photographic rendition of {subject}, dramatic golden hour backlight, intricate textures, photorealistic materials, volumetric lighting, high dynamic range, octane render quality."),
    ("Flux.1 Dev", "Ultra-sharp raw photo of {subject}, authentic micro-textures, natural daylight, photorealistic skin and material grain, medium format camera aesthetic, f/2.8 lens."),
    ("ChatGPT 4o", "Atue como um Engenheiro de Prompts especialista. Crie uma estratégia completa para {subject}, detalhando o tom de voz, persona do público-alvo, estrutura de copy AIDA e gatilhos mentais de escassez e autoridade."),
    ("Claude 3.5 Sonnet", "Analise e otimize o seguinte conceito para {subject}: forneça um plano passo a passo com análise SWOT, sugestões de posicionamento de mercado e 5 variações de títulos persuasivos para campanhas de alta conversão."),
    ("Sora Video", "Cinematic drone tracking shot of {subject}, smooth motion, realistic fluid dynamics, warm golden hour atmospheric haze, 60fps 4k photorealistic video generation."),
    ("Runway Gen-3", "Hyper-realistic slow motion clip showing {subject}, soft volumetric fog, dynamic camera pan, cinematic lighting, movie trailer aesthetic.")
]

SUBJECTS = {
    "comida-bebida": [
        "hambúrguer artesanal triplo com queijo cheddar derretido e bacon crocante em tábua de madeira rustica",
        "drink tropical artesanal em copo de cristal lapidado com gelo translúcido, pedaços de fruta fresca e hortelã",
        "xícara de cappuccino cremoso com arte latte de coração sobre pires de cerâmica artesanal em café aconchegante",
        "sobremesa gourmet de mousse de chocolate amargo com calda de frutas vermelhas e lâminas de ouro comestível"
    ],
    "moda-beleza": [
        "modelo em vestido de alta costura avant-garde com tecidos esvoaçantes em desfile de moda conceitual",
        "retrato de beleza editorial com maquiagem luminosa em tons dourados, pele radiante com poros visíveis e lábios nude",
        "modelo vestindo jaqueta de couro vintage e óculos de sol futuristas em cenário urbano noturno com luzes neon"
    ],
    "produtos-publicidade": [
        "garrafa de perfume de luxo em frasco de vidro facetado com gotas de água flutuando em fundo de mármore negro",
        "relógio cronógrafo esportivo em caixa de titânio sobre superfície de fibra de carbono com iluminação dramática",
        "fone de ouvido sem fio futurista flutuando levemente sobre base reflexiva com neblina e luzes LED suaves"
    ],
    "paisagens-cidades": [
        "cidade futurista utópica com arranha-céus espelhados, jardins suspensos e veículos voadores ao anoitecer",
        "paisagem de montanhas cobertas de neve sob o espetáculo da aurora boreal em tons verde e violeta cintilantes",
        "praia paradisíaca tropical com águas azul-turquesa cristalinas, areia branca e palmeiras inclinadas sob o sol"
    ],
    "animais": [
        "gato persa filhote brincando com um novelo de lã em quarto iluminado por luz matinal suave",
        "leão majestoso com juba volumosa ao vento olhando fixamente a savana africana durante o pôr do sol"
    ],
    "icones-ui": [
        "set de ícones 3D glassmorphism para aplicativo de finanças, cartões de crédito e gráficos em estética fosca",
        "ícone 3D de foguete espacial com rastro de fogo e nuvens fofas em estilo claymorphism vibrante"
    ],
    "objetos-arte": [
        "escultura abstrata de vidro soprado colorido com curvas orgânicas refletindo luz solar em galeria de arte",
        "composição de arte contemporânea com esferas espelhadas flutuando sobre estrutura minimalista de concreto"
    ]
}

def extract_array_from_bak(file_path, var_name):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    pattern = rf'const\s+{var_name}\s*=\s*(\[.*?\]);'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return []
    array_str = match.group(1)
    
    # Parse object entries
    entries = []
    item_matches = re.findall(r'\{\s*cat:\s*"([^"]+)",(?:\s*slug:\s*"([^"]+)",)?\s*img:\s*"([^"]+)",\s*prompt:\s*"((?:[^"\\]|\\.)*)"\s*\}', array_str)
    for cat, slug, img, prompt in item_matches:
        prompt_clean = prompt.replace('\\"', '"').replace('\\n', '\n')
        entries.append({
            'cat': cat,
            'slug': slug if slug else CATEGORY_SLUGS.get(cat, 'objetos-arte'),
            'img': img,
            'prompt': prompt_clean
        })
    return entries

def build():
    print("Extraindo prompts originais de main.js.bak...")
    orig_free = extract_array_from_bak(BAK_FILE, "promptData")
    orig_pago = extract_array_from_bak(BAK_FILE, "promptDataPago")
    
    print(f"Originais Gratuitos encontrados: {len(orig_free)}")
    print(f"Originais Pagos encontrados: {len(orig_pago)}")
    
    all_prompts = []
    
    # 1. Add original free prompts
    for idx, item in enumerate(orig_free):
        cat_slug = CATEGORY_SLUGS.get(item['cat'], 'objetos-arte')
        all_prompts.append({
            'cat': item['cat'],
            'slug': cat_slug,
            'img': f"prompts/{cat_slug}/{item['img']}",
            'prompt': item['prompt'],
            'isPro': False,
            'id': f"free_{idx+1:03d}"
        })
        
    # 2. Add original paid prompts
    for idx, item in enumerate(orig_pago):
        all_prompts.append({
            'cat': item['cat'],
            'slug': item['slug'],
            'img': f"prompts/pago/{item['slug']}/{item['img']}",
            'prompt': item['prompt'],
            'isPro': True,
            'id': f"orig_pago_{idx+1:03d}"
        })
        
    # 3. Add collected Telegram prompts
    telegram_items = []
    if os.path.exists(TELEGRAM_DATA):
        with open(TELEGRAM_DATA, 'r', encoding='utf-8') as f:
            telegram_items = json.load(f)
            
    print(f"Prompts coletados do Telegram: {len(telegram_items)}")
    for idx, item in enumerate(telegram_items):
        all_prompts.append({
            'cat': item['cat'],
            'slug': item['slug'],
            'img': f"prompts/pago/{item['slug']}/{item['img']}",
            'prompt': item['prompt'],
            'isPro': True,
            'id': f"telegram_{idx+1:04d}"
        })

    print(f"Total base compilado: {len(all_prompts)} prompts (Gratuitos: {len(orig_free)}, Pagos: {len(all_prompts) - len(orig_free)})")

    # 4. Fill up to 850 total prompts
    target_count = 850
    existing_images = [p['img'] for p in all_prompts if os.path.exists(os.path.join(BASE_DIR, p['img'].replace('/', '\\')))]
    if not existing_images:
        existing_images = [p['img'] for p in all_prompts]

    counter = len(all_prompts) + 1
    while len(all_prompts) < target_count:
        cat_info = random.choice(CATEGORIES)
        slug = cat_info["slug"]
        cat_name = cat_info["name"]
        
        subj_list = SUBJECTS.get(slug, SUBJECTS["objetos-arte"])
        subj = random.choice(subj_list)
        tool_name, template = random.choice(PROMPT_TEMPLATES)
        
        prompt_text = f"[{tool_name}] " + template.format(subject=subj)
        img_path = random.choice(existing_images)
            
        all_prompts.append({
            'cat': cat_name,
            'slug': slug,
            'img': img_path,
            'prompt': prompt_text,
            'isPro': True,
            'id': f"ext_{counter:04d}"
        })
        counter += 1

    print(f"Total final de prompts na biblioteca: {len(all_prompts)}")
    
    js_content = f"// PromptHub - Dataset completo com {len(orig_free)} Gratuitos e {len(all_prompts) - len(orig_free)} Premium\n"
    js_content += f"const ALL_PROMPTS_DATA = {json.dumps(all_prompts, ensure_ascii=False, indent=2)};\n"
    
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Arquivo JS gerado com sucesso em: {OUTPUT_JS}")

if __name__ == '__main__':
    build()
