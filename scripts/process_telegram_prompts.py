import os
import re
import shutil
import json

BASE_DIR = r"p:\LandingPage-PromptHub"
COLETA_DIR = os.path.join(BASE_DIR, "PromptHub_coleta")
PROMPTS_DEST_DIR = os.path.join(BASE_DIR, "prompts")
PAGO_DEST_DIR = os.path.join(PROMPTS_DEST_DIR, "pago")

CATEGORY_MAP = {
    'comida-bebida': 'Comida & Bebida',
    'moda-beleza': 'Moda & Beleza',
    'produtos-publicidade': 'Produtos & Publicidade',
    'paisagens-cidades': 'Paisagens & Cidades',
    'animais': 'Animais',
    'icones-ui': 'Icones & UI',
    'objetos-arte': 'Objetos & Arte'
}

KEYWORDS = {
    'comida-bebida': ['food', 'drink', 'coffee', 'ice cream', 'fruit', 'burger', 'cocktail', 'dish', 'plate', 'breakfast', 'chocolate', 'latte', 'juice', 'gummy', 'tea', 'oil', 'marshmallow', 'martini', 'croissant', 'avocado', 'grapes', 'barbecue', 'wine'],
    'moda-beleza': ['fashion', 'dress', 'hair', 'model', 'lipstick', 'vogue', 'outfit', 'beauty', 'skin', 'jacket', 'balenciaga', 'portrait', 'makeup', 'sunglasses', 'heels', 'accessories', 'woman', 'shirt', 'peonies', 'lingerie', 'suit', 'couch', 'jewelry'],
    'produtos-publicidade': ['product', 'ad', 'advertising', 'rolex', 'bottle', 'package', 'mockup', 'commercial', 'car', 'device', 'brand', 'nike', 'diffuser', 'mercedes', 'camaro', 'watch', 'sculpture', 'gucci', 'packaging', 'poster', 'soda', 'can', 'phone'],
    'paisagens-cidades': ['city', 'landscape', 'desert', 'sunset', 'ocean', 'street', 'sky', 'mountain', 'beach', 'architecture', 'building', 'dubai', 'storm', 'lightning', 'rooftop', 'futuristic city', 'waterfall', 'subway', 'park', 'nature', 'forest', 'island'],
    'animais': ['cat', 'dog', 'animal', 'pet', 'kitten', 'horse', 'bird', 'lion', 'tiger', 'puppy', 'bear', 'owl', 'rabbit', 'peeking', 'savannah', 'wildlife', 'fauna'],
    'icones-ui': ['icon', 'ui', '3d render', 'app icon', 'ios desktop icons', 'interface', 'button', 'badge', 'logo design', 'minimal icon', 'symbol', 'vector']
}

def clean_prompt_text(text):
    if not text:
        return ""
    text = re.sub(r'^(?:0%\s*)+', '', text)
    text = re.sub(r'\d+K?\s+\d{2}:\d{2}\s*$', '', text)
    text = re.sub(r'Leave a comment.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Subscribe!.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Join:\s*@\S+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Boost.*', '', text, flags=re.IGNORECASE)
    lines = [line.strip() for line in text.split('\n') if line.strip() and not line.strip().startswith('✦')]
    cleaned = ' '.join(lines)
    return cleaned.strip()

def detect_category(text, default_cat='objetos-arte'):
    lower_text = text.lower()
    for cat, words in KEYWORDS.items():
        for word in words:
            if word in lower_text:
                return cat
    return default_cat

def process():
    print("Iniciando varredura e processamento de prompts...")
    processed_prompts = []
    seen_keys = set()
    
    count = 0
    for root, dirs, files in os.walk(COLETA_DIR):
        img_files = sorted([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
        for img in img_files:
            base_name = os.path.splitext(img)[0]
            txt_file = os.path.join(root, base_name + ".txt")
            
            prompt_text = ""
            if os.path.exists(txt_file):
                try:
                    with open(txt_file, 'r', encoding='utf-8', errors='ignore') as tf:
                        prompt_text = clean_prompt_text(tf.read())
                except Exception as e:
                    pass
            
            if not prompt_text:
                folder_name = os.path.basename(root)
                prompt_text = f"High quality AI prompt collection from {folder_name} - Prompt #{base_name}"
            
            slug = detect_category(prompt_text)
            cat_name = CATEGORY_MAP.get(slug, 'Objetos & Arte')
            
            dest_dir = os.path.join(PAGO_DEST_DIR, slug)
            os.makedirs(dest_dir, exist_ok=True)
            
            img_rel_name = f"coleta_{count:04d}.jpg"
            src_img_path = os.path.join(root, img)
            dest_img_path = os.path.join(dest_dir, img_rel_name)
            
            shutil.copy2(src_img_path, dest_img_path)
            
            item = {
                'cat': cat_name,
                'slug': slug,
                'img': img_rel_name,
                'prompt': prompt_text,
                'isPro': True,
                'group': os.path.basename(root)
            }
            
            key = f"{slug}_{prompt_text[:50]}"
            if key not in seen_keys:
                seen_keys.add(key)
                processed_prompts.append(item)
                count += 1

    print(f"Coletados {count} prompts dos grupos do Telegram!")
    
    # Save output dataset json file
    output_json = os.path.join(BASE_DIR, "js", "telegram_coleta_data.json")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(processed_prompts, f, ensure_ascii=False, indent=2)
    print(f"Dataset salvo em {output_json}")

if __name__ == '__main__':
    process()
