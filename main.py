import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
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
ADMIN_IDS = [int(i.strip()) for i in os.getenv("ADMIN_ID").split(",")]
ANALYTICS_CHANNEL_ID = int(os.getenv("ANALYTICS_CHANNEL_ID"))

dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=TOKEN)
CHANNEL_ID = -1003898425915

start_photo_id = None


# ─── Состояния ───────────────────────────────────────────────
class Broadcast(StatesGroup):
    waiting_text = State()


class BroadcastByID(StatesGroup):
    waiting_ids = State()
    waiting_message = State()


# ─── Вспомогательная функция аналитики ───────────────────────
def user_label(user: types.User) -> str:
    full_name = user.full_name or "Nomsiz"
    username = f"@{user.username}" if user.username else "username yo'q"
    return f"👤 <b>{full_name}</b> ({username})\n🆔 <code>{user.id}</code>"


async def send_analytics(text: str):
    try:
        await bot.send_message(
            chat_id=ANALYTICS_CHANNEL_ID,
            text=text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[Analytics error]: {e}")


# ─── /start ──────────────────────────────────────────────────
@dp.message(CommandStart())
async def start_command(message: types.Message):
    global start_photo_id
    user = message.from_user

    add_user(
        user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username
    )

    kb = admin_keyboard() if user.id in ADMIN_IDS else main_menu_keyboards()

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

    await send_analytics(
        f"🆕 <b>Yangi /start</b>\n"
        f"{user_label(user)}"
    )


# ─── Biz Haqimizda ───────────────────────────────────────────
@dp.message(F.text == "📖 Biz Haqimizda")
async def about_us_command(message: types.Message):
    await message.answer(TEXTS["about_us"], parse_mode="HTML")

    await send_analytics(
        f"📖 <b>\"Biz Haqimizda\" tugmasini bosdi</b>\n"
        f"{user_label(message.from_user)}"
    )


# ─── Obuna bo'lish ────────────────────────────────────────────
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

    await send_analytics(
        f"⭐️ <b>\"Obuna bo'lish\" tugmasini bosdi</b> (hali to'lamadi)\n"
        f"{user_label(message.from_user)}"
    )


# ─── Pre-checkout ─────────────────────────────────────────────
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    await send_analytics(
        f"💳 <b>\"To'lash\" tugmasini bosdi</b> (hali to'lov o'tmadi)\n"
        f"{user_label(pre_checkout_query.from_user)}"
    )


# ─── Успешная оплата ──────────────────────────────────────────
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

    await send_analytics(
        f"✅ <b>To'lov muvaffaqiyatli amalga oshirildi!</b>\n"
        f"{user_label(message.from_user)}\n"
        f"💰 Summa: {message.successful_payment.total_amount // 100} {message.successful_payment.currency}"
    )


# ─── Рассылка всем ────────────────────────────────────────────
@dp.message(F.text == "📢 Rassylka", F.from_user.id.in_(ADMIN_IDS))
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer("✍️ Rassylka uchun matn yoki 📸 rasm bilan matn yuboring:")
    await state.set_state(Broadcast.waiting_text)


@dp.message(Broadcast.waiting_text, F.from_user.id.in_(ADMIN_IDS), F.photo)
async def broadcast_send_photo(message: types.Message, state: FSMContext):
    await state.clear()
    users = get_all_users()
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    success, failed = 0, 0

    for user_id in users:
        try:
            await bot.send_photo(user_id, photo=photo_id, caption=caption, parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    await message.answer("✅ Rassylka barcha foydalanuvchilarga yuborildi!", reply_markup=admin_keyboard())


@dp.message(Broadcast.waiting_text, F.from_user.id.in_(ADMIN_IDS), F.text)
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

    await message.answer("✅ Rassylka barcha foydalanuvchilarga yuborildi!", reply_markup=admin_keyboard())


# ─── Рассылка по ID ───────────────────────────────────────────
@dp.message(F.text == "🎯 ID bo'yicha Rassylka", F.from_user.id.in_(ADMIN_IDS))
async def broadcast_by_id_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📋 Foydalanuvchi ID larini kiriting (vergul bilan ajrating):\n\n"
        "<i>Misol: 123456789, 987654321, 111222333</i>",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastByID.waiting_ids)


@dp.message(BroadcastByID.waiting_ids, F.from_user.id.in_(ADMIN_IDS))
async def broadcast_by_id_get_ids(message: types.Message, state: FSMContext):
    raw = message.text.replace(" ", "")
    parts = raw.split(",")
    valid_ids = []
    invalid = []

    for part in parts:
        try:
            valid_ids.append(int(part))
        except ValueError:
            invalid.append(part)

    if not valid_ids:
        await message.answer("❌ Hech qanday to'g'ri ID topilmadi. Qaytadan kiriting:")
        return

    await state.update_data(target_ids=valid_ids)

    info = f"✅ {len(valid_ids)} ta ID qabul qilindi."
    if invalid:
        info += f"\n⚠️ Noto'g'ri: {', '.join(invalid)}"

    await message.answer(f"{info}\n\n✍️ Endi xabarni yuboring (matn yoki 📸 rasm):")
    await state.set_state(BroadcastByID.waiting_message)


@dp.message(BroadcastByID.waiting_message, F.from_user.id.in_(ADMIN_IDS), F.photo)
async def broadcast_by_id_send_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_ids = data.get("target_ids", [])
    await state.clear()

    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    success, failed = 0, 0

    for user_id in target_ids:
        try:
            await bot.send_photo(user_id, photo=photo_id, caption=caption, parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ Yuborildi: {success}\n❌ Yetkazilmadi: {failed}",
        reply_markup=admin_keyboard()
    )


@dp.message(BroadcastByID.waiting_message, F.from_user.id.in_(ADMIN_IDS), F.text)
async def broadcast_by_id_send_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_ids = data.get("target_ids", [])
    await state.clear()

    success, failed = 0, 0

    for user_id in target_ids:
        try:
            await bot.send_message(user_id, message.text, parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ Yuborildi: {success}\n❌ Yetkazilmadi: {failed}",
        reply_markup=admin_keyboard()
    )


# ─── Запуск ───────────────────────────────────────────────────
async def main():
    init_db()
    print("bot is version 0.2.1")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())