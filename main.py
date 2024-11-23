
# Online Python - IDE, Editor, Compiler, Interpreter

import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

# Bot tokenini kiritish
TOKEN = "6610643698:AAEcghZC1iirJl4-BvfklM3XlZN3uf395yQ"
CHANNEL_ID = "@hidencoin"  # Kanal foydalanuvchi nomi

# Botni ishga tushirish
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Ma'lumotlar bazasini sozlash
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    invited_by INTEGER,
    invites INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0
)
""")
conn.commit()

# Kanalga obuna tekshirish funksiyasi
async def check_subscription(user_id):
    member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    return member.status in ["member", "administrator", "creator"]

# Boshlash buyruqni qayta ishlash
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    # Kanalga obuna bo'lganligini tekshirish
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}")
        )
        await message.answer(
            "Botdan foydalanish uchun avval kanalimizga obuna bo‘ling!", reply_markup=keyboard
        )
        return

    # Foydalanuvchini bazaga qo'shish yoki yangilash
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        invited_by = int(args) if args.isdigit() else None
        cursor.execute("INSERT INTO users (user_id, invited_by) VALUES (?, ?)", (user_id, invited_by))
        
        # Taklif qilgan foydalanuvchi hisobini yangilash
        if invited_by:
            cursor.execute("UPDATE users SET invites = invites + 1, points = points + 1 WHERE user_id = ?", (invited_by,))
        conn.commit()

    # Ulashish xavolasini yuborish
    share_link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Xavolani ulashish", url=share_link)
    )
    await message.answer(
        f"Xush kelibsiz, {message.from_user.first_name}! Sizning xavolangiz:\n{share_link}\n\n"
        "Ushbu xavolani do'stlaringiz bilan ulashing va taklif qilingan foydalanuvchilar orqali ball to'plang!",
        reply_markup=keyboard
    )

# Taklif qilingan odamlar va ballar sonini ko'rsatish
@dp.message_handler(commands=["stats"])
async def stats_command(message: types.Message):
    user_id = message.from_user.id

    # Kanalga obuna bo'lganligini tekshirish
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}")
        )
        await message.answer(
            "Statistikani ko‘rish uchun avval kanalimizga obuna bo‘ling!", reply_markup=keyboard
        )
        return

    cursor.execute("SELECT invites, points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        invites, points = result
        await message.answer(f"Siz {invites} ta odamni taklif qildingiz va {points} ball to'pladingiz!")
    else:
        await message.answer("Hali taklif qilingan odamlar yoki ballar yo‘q.")

# Xabarlar reaksiyalarini qayta ishlash
@dp.message_handler(content_types=["text"])
async def track_reactions(message: types.Message):
    user_id = message.from_user.id

    # Faqat kanal xabarlarida ball beriladi
    if message.chat.type == "channel" and message.chat.username == CHANNEL_ID.lstrip("@"):
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            # Har bir faoliyat uchun 5 ball qo'shish
            cursor.execute("UPDATE users SET points = points + 5 WHERE user_id = ?", (user_id,))
            conn.commit()

# Botni ishga tushirish
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
