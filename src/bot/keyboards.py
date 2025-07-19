from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(user_trial_used: bool):
    builder = InlineKeyboardBuilder()
    if not user_trial_used:
        builder.add(InlineKeyboardButton(text="🎁 Пробный период", callback_data="trial"))
    builder.add(InlineKeyboardButton(text="🔑️ Подписка", callback_data="subscription_info"))
    builder.add(InlineKeyboardButton(text="🤝 Пригласить друга", callback_data="ref_program"))
    builder.add(InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"))

    from src.bot.handlers.privacy_policy import page

    builder.add(
        InlineKeyboardButton(
            text="📄 Пользовательское соглашение", callback_data="privacy_policy", url=page["url"]
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def back_to_main_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Главное меню", callback_data="back_to_main"))
    return builder.as_markup()


def trial_confirmation_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Получить", callback_data="get_trial"))
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    builder.adjust(2)
    return builder.as_markup()


def tariff_selection_kb(tariffs: list):
    builder = InlineKeyboardBuilder()
    for tariff in tariffs:
        if tariff.price == 0:
            continue
        text = f"{tariff.duration_days} дней - {tariff.price}₽"
        callback_data = f"tariff_{tariff.id}"
        builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    builder.adjust(1)
    return builder.as_markup()


def subscription_info_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Купить/продлить", callback_data="select_tariff"))
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    builder.adjust(2)
    return builder.as_markup()


def referral_info_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    return builder.as_markup()


def help_kb():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Инструкция", callback_data="send_instruction"),
        InlineKeyboardButton(text="Поддержка", callback_data="send_support"),
    )
    builder.add(InlineKeyboardButton(text="Главное меню", callback_data="back_to_main"))
    builder.adjust(2)
    return builder.as_markup()
