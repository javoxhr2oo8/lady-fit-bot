from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboards():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📖 Biz Haqimizda"),
                KeyboardButton(text="⭐️ Obuna bo'lish"),
            ]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📖 Biz Haqimizda"),
                KeyboardButton(text="⭐️ Obuna bo'lish"),
            ],
            [
                KeyboardButton(text="📢 Rassylka"),
                KeyboardButton(text="🎯 ID bo'yicha Rassylka"),
            ]
        ],
        resize_keyboard=True
    )