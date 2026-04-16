from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboards():
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📖 Biz Haqimizda"),
                KeyboardButton(text="⭐️ Obuna bo'lish"),
            ]
        ],
        resize_keyboard=True
    )
    return main_menu

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📖 Biz Haqimizda"),
                KeyboardButton(text="⭐️ Obuna bo'lish"),
            ],
            [
                KeyboardButton(text="📢 Rassylka"),
            ]
        ],
        resize_keyboard=True
    )