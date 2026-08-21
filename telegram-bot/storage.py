import json
import shutil
from datetime import datetime
from pathlib import Path

from config import (
    PROMPTS_IMAGES_DIR,
    PROMPTS_JS_FILE,
    IMAGES_DIR,
    DATA_DIR,
)


def get_group_folder(group_name):
    """Cria e retorna a pasta do grupo."""
    # Limpar nome da pasta
    safe_name = group_name.lower().replace(" ", "_").replace("-", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    folder = PROMPTS_IMAGES_DIR / safe_name
    folder.mkdir(exist_ok=True)
    return folder, safe_name


def load_existing_prompts():
    """Carrega prompts existentes do arquivo JS do site."""
    if not PROMPTS_JS_FILE.exists():
        return []

    try:
        content = PROMPTS_JS_FILE.read_text(encoding="utf-8")
        # Extrair JSON do JS (remove "window.PROMPTS_LIBRARY = " e ";")
        json_str = content.replace("window.PROMPTS_LIBRARY = ", "").rstrip().rstrip(";")
        return json.loads(json_str)
    except Exception as e:
        print(f"Erro ao ler prompts existentes: {e}")
        return []


def save_to_site_format(image_path, prompt_text, group_title, link="", date=""):
    """
    Salva um prompt no formato do site.
    Retorna (sucesso, mensagem, dados_salvos)
    """
    # Carregar prompts existentes
    prompts = load_existing_prompts()

    # Criar pasta do grupo
    group_folder, group_slug = get_group_folder(group_title)

    # Contar imagens existentes no grupo para gerar nome unico
    existing = list(group_folder.glob("pair_*.jpg"))
    next_num = len(existing) + 1
    img_filename = f"pair_{next_num:04d}.jpg"
    img_relative = f"prompts_library/{group_slug}/{img_filename}"

    # Copiar imagem para a pasta do site
    dest = group_folder / img_filename
    try:
        shutil.copy2(image_path, dest)
    except Exception as e:
        return False, f"Erro ao copiar imagem: {e}", None

    # Criar entrada no formato do site
    entry = {
        "img": img_relative,
        "prompt": prompt_text,
        "grupo": group_slug,
        "categoria": "geral",
        "modelo": "N/A",
        "link": link,
        "data": date or datetime.now().strftime("%B %d"),
    }

    # Adicionar a lista
    prompts.append(entry)

    # Salvar no arquivo JS
    js_content = "window.PROMPTS_LIBRARY = " + json.dumps(
        prompts, ensure_ascii=False, indent=None
    ) + ";"

    PROMPTS_JS_FILE.write_text(js_content, encoding="utf-8")

    return True, f"Prompt salvo: {img_relative}", entry


def save_backup(image_path, prompt_text, group_title, message_id, chat_id):
    """Salva backup na pasta local do bot."""
    # Copiar para pasta de backup
    filename = f"{chat_id}_{message_id}.jpg"
    backup_path = IMAGES_DIR / filename
    try:
        shutil.copy2(image_path, backup_path)
    except Exception:
        pass

    # Salvar JSON de backup
    backup_file = DATA_DIR / "backup_prompts.json"
    if backup_file.exists():
        with open(backup_file, "r", encoding="utf-8") as f:
            backup_data = json.load(f)
    else:
        backup_data = []

    backup_data.append({
        "message_id": message_id,
        "chat_id": chat_id,
        "chat_title": group_title,
        "text": prompt_text,
        "image_backup": str(backup_path),
        "collected_at": datetime.now().isoformat(),
    })

    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)


def get_stats():
    """Retorna estatisticas da coleta."""
    prompts = load_existing_prompts()
    groups = {}
    for p in prompts:
        g = p.get("grupo", "outro")
        groups[g] = groups.get(g, 0) + 1

    return {
        "total": len(prompts),
        "groups": groups,
    }


def list_prompts(limit=10):
    """Lista os ultimos prompts coletados."""
    prompts = load_existing_prompts()
    return prompts[-limit:] if prompts else []


def export_to_hubvision():
    """Exporta prompts no formato compativel com o site."""
    return load_existing_prompts()
