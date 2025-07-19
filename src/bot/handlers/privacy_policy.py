from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery
from telegraph import Telegraph

from src.bot.keyboards import back_to_main_kb

router = Router()

BOT_DIR = Path(__file__).parent.parent
HTML_PATH = BOT_DIR / "privacy_policy.html"
PRIVACY_POLICY_CONTENT = HTML_PATH.read_text(encoding="utf-8")

telegraph = Telegraph()
account = telegraph.create_account(short_name="UnbrokenVPNBot")
page = telegraph.create_page(
    title="Пользовательское соглашение",
    author_name="UnbrokenVPNBot",
    html_content=PRIVACY_POLICY_CONTENT,
)


@router.callback_query(F.data == "privacy_policy")
async def send_privacy_policy(callback: CallbackQuery):
    """
    Обработчик для вывода пользовательского соглашения через Telegra.ph
    """
    text = (
        "📄 <b>Пользовательское соглашение</b>\n\n"
        "Ознакомьтесь с полными условиями использования нашего бота по ссылке ниже:\n"
        f"<a href=\"{page['url']}\">{page['url']}</a>"
    )
    await callback.message.edit_text(
        text, disable_web_page_preview=True, reply_markup=back_to_main_kb()
    )
