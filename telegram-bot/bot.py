"""
HubVision Telegram Bot - Coletor de Prompts
============================================
"""

import json
import logging
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote_plus

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN, PROMPTS_IMAGES_DIR, PROMPTS_JS_FILE

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

daily_count = 0
DAILY_LIMIT = 30


def translate_to_english(text):
    """Traduz para ingles."""
    if not text:
        return text
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={quote_plus(text)}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urlopen(req, timeout=10)
        data = json.loads(response.read().decode())
        translated = "".join([s[0] for s in data[0] if s[0]])
        return translated if translated else text
    except Exception as e:
        logger.error(f"Erro ao traduzir: {e}")
        return text


def clean_prompt(text):
    """Limpa o prompt removendo emojis, hashtags, links."""
    if not text:
        return ""
    # Remove ALL emojis comprehensively
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U0001F900-\U0001F9FF"  # supplemental
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\u200D"                 # zero width joiner
        "\u2640-\u2642"          # gender symbols
        "\u2600-\u2B55"          # misc symbols
        "\u23CF"                 # eject
        "\u23E9-\u23F3"          # player controls
        "\u23F8-\u23FA"          # player controls
        "\uFE0F"                 # variation selector
        "\u2934-\u2935"          # arrows
        "\u25AA-\u25FE"          # geometric shapes
        "\u2614-\u2615"          # umbrella, hot beverage
        "\u2648-\u2653"          # zodiac
        "\u267F"                 # wheelchair
        "\u2693"                 # anchor
        "\u26A1"                 # high voltage
        "\u26AA-\u26AB"          # circles
        "\u26BD-\u26BE"          # sports
        "\u26C4-\u26C5"          # weather
        "\u26CE"                 # Ophiuchus
        "\u26D4"                 # no entry
        "\u26EA"                 # church
        "\u26F2-\u26F3"          # fountain, golf
        "\u26F5"                 # sailboat
        "\u26FA"                 # tent
        "\u26FD"                 # fuel pump
        "\u2702"                 # scissors
        "\u2705"                 # check mark
        "\u2708-\u270D"          # hand, pencil
        "\u270F"                 # pencil
        "\u2764"                 # heart
        "\u2766-\u2767"          # heart ornaments
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    text = re.sub(r'#\S+', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'^Prompt:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Prompt\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_group_folder(group_name):
    """Cria pasta do grupo."""
    safe_name = group_name.lower().replace(" ", "_").replace("-", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    folder = PROMPTS_IMAGES_DIR / safe_name
    folder.mkdir(exist_ok=True)
    return folder, safe_name


def load_existing_prompts():
    """Carrega prompts do JS."""
    if not PROMPTS_JS_FILE.exists():
        return []
    try:
        content = PROMPTS_JS_FILE.read_text(encoding="utf-8")
        json_str = content.replace("window.PROMPTS_LIBRARY = ", "").rstrip().rstrip(";")
        return json.loads(json_str)
    except:
        return []


def save_to_library(image_path, prompt_text, group_title, link=""):
    """Salva na biblioteca."""
    prompts = load_existing_prompts()
    group_folder, group_slug = get_group_folder(group_title)
    existing = list(group_folder.glob("pair_*.jpg"))
    next_num = len(existing) + 1
    img_filename = f"pair_{next_num:04d}.jpg"
    img_relative = f"prompts_library/{group_slug}/{img_filename}"

    dest = group_folder / img_filename
    try:
        shutil.copy2(image_path, dest)
    except Exception as e:
        logger.error(f"Erro ao copiar imagem: {e}")
        return False

    entry = {
        "img": img_relative,
        "prompt": prompt_text,
        "grupo": group_slug,
        "categoria": "geral",
        "modelo": "N/A",
        "link": link,
        "data": datetime.now().strftime("%B %d"),
    }

    prompts.append(entry)

    js_content = "window.PROMPTS_LIBRARY = " + json.dumps(
        prompts, ensure_ascii=False, indent=None
    ) + ";"

    PROMPTS_JS_FILE.write_text(js_content, encoding="utf-8")
    return True


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Boas-vindas."""
    await update.message.reply_text(
        "HubVision Prompt Collector\n"
        "========================\n\n"
        "Encaminhe mensagens com prompt + imagem\n"
        "ou cole o texto direto no chat.\n\n"
        "Prompts sao traduzidos para ingles!"
    )


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista prompts."""
    prompts = load_existing_prompts()
    if not prompts:
        await update.message.reply_text("Nenhum prompt ainda.")
        return
    text = f"Total: {len(prompts)} prompts\n\n"
    for p in prompts[-5:]:
        preview = p["prompt"][:60] + "..." if len(p["prompt"]) > 60 else p["prompt"]
        text += f"- {preview}\n\n"
    await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens."""
    global daily_count

    message = update.effective_message
    if not message:
        return

    if daily_count >= DAILY_LIMIT:
        await message.reply_text("Limite diario atingido. Tente amanha.")
        return

    user = update.effective_user
    text = message.text or message.caption or ""
    has_photo = bool(message.photo)

    logger.info(f"Mensagem recebida: chat={update.effective_chat.title}, tipo={update.effective_chat.type}, foto={has_photo}, texto={text[:80]}...")
    logger.info(f"forward_origin={getattr(message, 'forward_origin', None)}, forward_from_chat={getattr(message, 'forward_from_chat', None)}")
    logger.info(f"message.text={message.text}, message.caption={message.caption}")

    if not text and not has_photo:
        logger.info("Ignorado: sem texto e sem foto")
        return

    cleaned = clean_prompt(text)
    translated = translate_to_english(cleaned) if cleaned else ""

    if has_photo and translated:
        try:
            photo = message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            temp_path = Path(f"temp_{message.message_id}.jpg")
            await file.download_to_drive(str(temp_path))

            chat_title = "prompts"
            # v22+ API: forward_origin
            if hasattr(message, 'forward_origin') and message.forward_origin:
                origin = message.forward_origin
                if hasattr(origin, 'chat') and origin.chat:
                    chat_title = origin.chat.title or "prompts"
                elif hasattr(origin, 'sender_user_name'):
                    chat_title = origin.sender_user_name or "prompts"
            elif hasattr(message, 'forward_from_chat') and message.forward_from_chat:
                chat_title = message.forward_from_chat.title or "prompts"
            elif update.effective_chat.type == "private":
                chat_title = user.username or "my_prompts"
            else:
                chat_title = update.effective_chat.title or "prompts"

            logger.info(f"Salvando prompt do grupo: {chat_title}")

            success = save_to_library(
                image_path=str(temp_path),
                prompt_text=translated,
                group_title=chat_title,
                link=""
            )

            temp_path.unlink(missing_ok=True)

            if success:
                daily_count += 1
                await message.reply_text(
                    f"Prompt salvo!\n\n"
                    f"EN: {translated[:200]}"
                )
                logger.info(f"Salvo: {chat_title}")
            else:
                await message.reply_text("Erro ao salvar.")

        except Exception as e:
            logger.error(f"Erro: {e}")
            await message.reply_text(f"Erro: {str(e)}")

    elif translated and not has_photo:
        try:
            chat_title = user.username or "text_prompts"
            group_folder, group_slug = get_group_folder(chat_title)
            prompts = load_existing_prompts()
            entry = {
                "img": "",
                "prompt": translated,
                "grupo": group_slug,
                "categoria": "text",
                "modelo": "N/A",
                "link": "",
                "data": datetime.now().strftime("%B %d"),
            }
            prompts.append(entry)
            js_content = "window.PROMPTS_LIBRARY = " + json.dumps(
                prompts, ensure_ascii=False, indent=None
            ) + ";"
            PROMPTS_JS_FILE.write_text(js_content, encoding="utf-8")
            daily_count += 1
            await message.reply_text(f"Texto salvo!\n\nEN: {translated[:200]}")
        except Exception as e:
            await message.reply_text(f"Erro: {str(e)}")

    elif has_photo and not translated:
        await message.reply_text("Foto sem texto. Envie com o prompt.")


async def post_init(application: Application):
    bot = application.bot
    me = await bot.get_me()
    logger.info(f"Bot: @{me.username}")


def main():
    if BOT_TOKEN == "SEU_TOKEN_AQUI":
        print("ERRO: Configure BOT_TOKEN!")
        sys.exit(1)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("=" * 40)
    print("HubVision Prompt Collector")
    print("=" * 40)
    print("Aguardando mensagens...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
