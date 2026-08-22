"""Collect prompts from Telegram chats when the owner reacts to a message."""

import json
import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient, events, functions, types, utils

from bot import clean_prompt, load_existing_prompts, translate_to_english

BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent
PROMPTS_DIR = PROJECT_DIR / "prompts_library"
PROMPTS_FILE = PROJECT_DIR / "js" / "prompts_library.js"
PROCESSED_FILE = BASE_DIR / "processed_reactions.json"
SESSION_FILE = BASE_DIR / "hubvision_user"

load_dotenv(BASE_DIR / ".env")
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("hubvision.telegram")


def required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Configure {name} em telegram-bot/.env")
    return value


API_ID = int(required_env("TELEGRAM_API_ID"))
API_HASH = required_env("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE", "").strip() or None
FOLDER_NAME = os.getenv("TELEGRAM_FOLDER", "PROMPTS/IA").strip()
COLLECT_REACTIONS = [r.strip() for r in os.getenv("TELEGRAM_COLLECT_REACTIONS", "🔥").split(",") if r.strip()]
if not COLLECT_REACTIONS:
    COLLECT_REACTIONS = ["🔥"]


def slugify(value):
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.lower()).strip("_")
    return value or "telegram"


def has_collect_reaction(reactions):
    return any(
        getattr(getattr(result, "reaction", None), "emoticon", None)
        in COLLECT_REACTIONS
        for result in (reactions.results or [])
    )


def load_processed():
    if not PROCESSED_FILE.exists():
        return set()
    try:
        return set(json.loads(PROCESSED_FILE.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        logger.warning("Indice de mensagens invalido; iniciando um novo indice")
        return set()


def save_processed(processed):
    PROCESSED_FILE.write_text(
        json.dumps(sorted(processed), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def save_library_entry(image_path, prompt, chat, message):
    group = chat.title or getattr(chat, "username", None) or str(chat.id)
    group_slug = slugify(group)
    group_dir = PROMPTS_DIR / "prompts_ia" / group_slug
    group_dir.mkdir(parents=True, exist_ok=True)
    number = len(list(group_dir.glob("pair_*.jpg"))) + 1
    destination = group_dir / f"pair_{number:04d}.jpg"
    destination.write_bytes(image_path.read_bytes())

    link = ""
    if getattr(chat, "username", None):
        link = f"https://t.me/{chat.username}/{message.id}"
    entry = {
        "img": destination.relative_to(PROJECT_DIR).as_posix(),
        "prompt": prompt,
        "grupo": group_slug,
        "categoria": "prompts_ia",
        "modelo": "N/A",
        "link": link,
        "data": datetime.now().strftime("%B %d"),
        "source_chat_id": chat.id,
        "source_message_id": message.id,
    }

    prompts = load_existing_prompts()
    prompts.append(entry)
    content = "window.PROMPTS_LIBRARY = " + json.dumps(
        prompts, ensure_ascii=False, separators=(",", ":")
    ) + ";"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=PROMPTS_FILE.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(PROMPTS_FILE)


async def folder_chat_ids(client):
    """Return chats explicitly included in the configured Telegram folder."""
    result = await client(functions.messages.GetDialogFiltersRequest())
    filters = getattr(result, "filters", result)
    available = []
    wanted = FOLDER_NAME.casefold()
    target = None
    for item in filters:
        title = getattr(getattr(item, "title", None), "text", "")
        available.append(title or "(sem nome)")
        if title.casefold() == wanted:
            target = item
            break
    if not target:
        options = ", ".join(available) or "nenhuma pasta personalizada"
        raise RuntimeError(
            f"Pasta Telegram nao encontrada: {FOLDER_NAME}. Disponiveis: {options}"
        )
    included = {utils.get_peer_id(peer) for peer in target.include_peers}
    folder_id = getattr(target, "id", None)
    async for dialog in client.iter_dialogs():
        if getattr(dialog, "folder_id", None) == folder_id:
            included.add(dialog.id)
    return included


async def main():
    client = TelegramClient(str(SESSION_FILE), API_ID, API_HASH)
    await client.start(phone=PHONE)
    owner = await client.get_me()
    monitored = await folder_chat_ids(client)
    processed = load_processed()
    logger.info("Conta autenticada: %s", getattr(owner, "username", owner.id))
    logger.info("Monitorando %d chats da pasta %s", len(monitored), FOLDER_NAME)

    async def owner_reacted(peer, message_id, reactions):
        if any(
            getattr(reaction, "chosen", False)
            for reaction in (reactions.results or [])
        ):
            return True
        try:
            current_message = await client.get_messages(peer, ids=message_id)
            current_reactions = getattr(current_message, "reactions", None)
            if current_reactions and any(
                getattr(reaction, "chosen", False)
                for reaction in (current_reactions.results or [])
            ):
                return True

            entity = await client.get_entity(peer)
            if getattr(entity, "broadcast", False):
                return False
            reaction_list = await client(
                functions.messages.GetMessageReactionsListRequest(
                    peer=peer, id=message_id, limit=100
                )
            )
            return any(
                getattr(item.peer_id, "user_id", None) == owner.id
                for item in (getattr(reaction_list, "reactions", None) or [])
            )
        except Exception as error:
            logger.warning("Nao foi possivel consultar autores da reacao: %s", error)
            return False

    @client.on(events.Raw(types.UpdateMessageReactions))
    async def on_raw_update(update):
        logger.info("Evento de reacao recebido: mensagem %s", update.msg_id)
        recent = update.reactions.recent_reactions or []
        exclusive_reaction = has_collect_reaction(update.reactions)
        chosen = (
            exclusive_reaction
            or await owner_reacted(update.peer, update.msg_id, update.reactions)
        )
        logger.info(
            "Resultados de reacao=%s",
            [
                {
                    "tipo": type(result).__name__,
                    "chosen": getattr(result, "chosen", None),
                    "count": getattr(result, "count", None),
                }
                for result in (update.reactions.results or [])
            ],
        )
        logger.info(
            "Conta autenticada id=%s; reacao_propria=%s; autores recebidos=%s",
            owner.id,
            chosen,
            [
                {
                    "tipo": type(reaction.peer_id).__name__,
                    "user_id": getattr(reaction.peer_id, "user_id", None),
                    "channel_id": getattr(reaction.peer_id, "channel_id", None),
                }
                for reaction in recent
            ],
        )
        reacted_by_owner = any(
            getattr(reaction.peer_id, "user_id", None) == owner.id
            for reaction in recent
        ) or chosen or exclusive_reaction
        if not reacted_by_owner:
            logger.info("Reacao nao atribuida a conta autenticada")
            return

        chat_id = utils.get_peer_id(update.peer)
        logger.info(
            "Reacao de coleta detectada no chat %s (exclusiva=%s)",
            chat_id,
            exclusive_reaction,
        )
        if chat_id not in monitored and not exclusive_reaction:
            logger.info("Chat fora da pasta configurada: %s", chat_id)
            return
        key = f"{chat_id}:{update.msg_id}"
        if key in processed:
            return

        message = await client.get_messages(update.peer, ids=update.msg_id)
        if not message or not message.photo or not message.raw_text:
            logger.info("Ignorado %s: sem imagem ou texto", key)
            processed.add(key)
            save_processed(processed)
            return

        cleaned = clean_prompt(message.raw_text)
        if not cleaned:
            logger.info("Ignorado %s: texto vazio apos limpeza", key)
            processed.add(key)
            save_processed(processed)
            return

        prompt = translate_to_english(cleaned)
        with tempfile.TemporaryDirectory(dir=BASE_DIR) as temporary_dir:
            image = await message.download_media(file=Path(temporary_dir) / "source.jpg")
            if not image:
                logger.warning("Falha ao baixar imagem %s", key)
                return
            chat = await client.get_entity(update.peer)
            save_library_entry(Path(image), prompt, chat, message)

        processed.add(key)
        save_processed(processed)
        logger.info("Prompt salvo: %s (%s)", key, getattr(chat, "title", None) or chat.id)

    await client.run_until_disconnected()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
