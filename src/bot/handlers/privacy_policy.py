import hashlib
import json
from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery
from telegraph import Telegraph

from src.bot.keyboards import back_to_main_kb

router = Router()

BOT_DIR = Path(__file__).parent.parent
HTML_PATH = BOT_DIR / "privacy_policy.html"
STORAGE_PATH = BOT_DIR / "telegraph_page.json"


PRIVACY_POLICY_CONTENT = HTML_PATH.read_text(encoding="utf-8")
content_hash = hashlib.sha256(PRIVACY_POLICY_CONTENT.encode("utf-8")).hexdigest()

telegraph = Telegraph()
_ = telegraph.create_account(short_name="UnbrokenVPNBot")

if STORAGE_PATH.exists():
    with STORAGE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    page_path = data["path"]
    last_hash = data.get("hash")

    if last_hash != content_hash:
        telegraph.edit_page(path=page_path, html_content=PRIVACY_POLICY_CONTENT)
        data["hash"] = content_hash
        with STORAGE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
else:
    # Первый запуск
    page = telegraph.create_page(
        title="Пользовательское соглашение",
        author_name="UnbrokenVPNBot",
        html_content=PRIVACY_POLICY_CONTENT,
    )
    page_path = page["path"]
    data = {"path": page_path, "hash": content_hash}
    with STORAGE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Итоговый URL для показа в боте
PRIVACY_POLICY_URL = f"https://telegra.ph/{page_path}"


@router.callback_query(F.data == "privacy_policy")
async def send_privacy_policy(callback: CallbackQuery):
    """
    Обработчик для показа пользовательского соглашения через Telegra.ph.
    Ссылка обновляется только при изменении файла privacy_policy.html.
    """
    text = (
        "📄 <b>Пользовательское соглашение</b>\n\n"
        "Ознакомьтесь с полными условиями использования нашего бота по ссылке ниже:\n"
        f'<a href="{PRIVACY_POLICY_URL}">{PRIVACY_POLICY_URL}</a>'
    )
    await callback.message.edit_text(
        text, disable_web_page_preview=True, reply_markup=back_to_main_kb()
    )
