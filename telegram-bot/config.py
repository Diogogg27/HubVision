import os
from pathlib import Path

# Bot API settings. Keep the token in the environment.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_IDS = []
REACTION_EMOJI = "👍"

PROJECT_DIR = Path(__file__).parent.parent
PROMPTS_IMAGES_DIR = PROJECT_DIR / "prompts_library"
PROMPTS_JS_FILE = PROJECT_DIR / "js" / "prompts_library.js"
DATA_DIR = Path(__file__).parent / "collected_prompts"
IMAGES_DIR = DATA_DIR / "images"
PROMPTS_FILE = DATA_DIR / "backup_prompts.json"

PROMPTS_IMAGES_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)
