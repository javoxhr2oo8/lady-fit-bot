import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, LabeledPrice
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from texts import TEXTS
from keyboards import main_menu_keyboards, admin_keyboard
from database import init_db, add_user, get_all_users

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=TOKEN)
CHANNEL_ID = -1003898425915

start_photo_id = None


class Broadcast(StatesGroup):
    waiting_text = State()


@dp.message(CommandStart())
async def start_command(message: types.Message):
    global start_photo_id

    add_user(message.from_user.id)

    kb = admin_keyboard() if message.from_user.id == ADMIN_ID else main_menu_keyboards()

    if start_photo_id:
        await message.answer_photo(
            photo=start_photo_id,
            caption=TEXTS["welcome"],
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        photo_path = "./images/jpg/start_photo.jpg"
        photo = FSInputFile(photo_path)
        response = await message.answer_photo(
            photo=photo,
            caption=TEXTS["welcome"],
            parse_mode="HTML",
            reply_markup=kb
        )
        start_photo_id = response.photo[-1].file_id


@dp.message(F.text == "📖 Biz Haqimizda")
async def about_us_command(message: types.Message):
    await message.answer(TEXTS["about_us"], parse_mode="HTML")


@dp.message(F.text == "⭐️ Obuna bo'lish")
async def payment_for_link(message: types.Message, bot: Bot):
    receipt = {
        "items": [
            {
                "title": "Kanalga obuna",
                "price": 500000,
                "count": 1,
                "code": "10305008004000000",
                "package_code": "1234567",
                "vat_percent": 0
            }
        ]
    }

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Obuna",
        description="To'lov qilish orqali bizning kanalimizga obuna bo'ling!",
        payload="sub_1",
        provider_token="387026696:LIVE:68b6df538f3347fe865a1402",
        currency="UZS",
        prices=[LabeledPrice(label="Obuna", amount=500000)],
        provider_data=json.dumps({"receipt": receipt}),
        start_parameter="sub-pay"
    )

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment_handler(message: types.Message, bot: Bot):
    invite_link = await bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1
    )
    
    await message.answer(
        f"✅ To'lov muvaffaqiyatli amalga oshirildi!\n\n"
        f"🔗 Mana sizning bir martalik havolangiz:\n{invite_link.invite_link}\n\n"
        f"⚠️ Havola faqat bir kishi uchun amal qiladi!"
    )


@dp.message(F.text == "📢 Rassylka", F.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer(
        "✍️ Rassylka uchun matn yoki 📸 rasm bilan matn yuboring:"
    )
    await state.set_state(Broadcast.waiting_text)


@dp.message(Broadcast.waiting_text, F.from_user.id == ADMIN_ID, F.photo)
async def broadcast_send_photo(message: types.Message, state: FSMContext):
    await state.clear()
    users = get_all_users()
    success, failed = 0, 0

    photo_id = message.photo[-1].file_id
    caption = message.caption or ""

    for user_id in users:
        try:
            await bot.send_photo(user_id, photo=photo_id, caption=caption, parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        # f"✅ Yuborildi: {success}\n❌ Yetkazilmadi: {failed}",
        "✅ Rassylka barcha foydalanuvchilarga yuborildi!",
        reply_markup=admin_keyboard()
    )


@dp.message(Broadcast.waiting_text, F.from_user.id == ADMIN_ID, F.text)
async def broadcast_send_text(message: types.Message, state: FSMContext):
    await state.clear()
    users = get_all_users()
    success, failed = 0, 0

    for user_id in users:
        try:
            await bot.send_message(user_id, message.text, parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        # f"✅ Yuborildi: {success}\n❌ Yetkazilmadi: {failed}",
        "✅ Rassylka barcha foydalanuvchilarga yuborildi!",
        reply_markup=admin_keyboard()
    )


async def main():
    init_db()
    print("bot is version 0.1.2")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())