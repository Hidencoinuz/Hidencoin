from datetime import datetime, timedelta
from telebot import TeleBot, types

bot = TeleBot("6610643698:AAEcghZC1iirJl4-BvfklM3XlZN3uf395yQ")

# Parametrlar
users = {}  # Foydalanuvchilar ma'lumotlari
MAX_HIDDEN_COINS = 2000000  # Maksimal ishlab chiqariladigan Hiden Coin
HIDDEN_COIN_TASK = 1  # Vazifa uchun coin
HIDDEN_COIN_DAILY = 1.3  # Kunlik mukofot
REFERRAL_COIN = 1  # Referal mukofoti
COIN_PRICES = [2.30, 1.15, 1.68, 2.50]  # Coin qiymatlari
current_price_index = 0  # Hozirgi qiymat indeksini kuzatish
price_last_updated = datetime.now()  # Qiymat oxirgi o'zgartirilgan vaqt
total_hidden_coins = 0  # Jami ishlab chiqarilgan coinlar
INACTIVITY_THRESHOLD_30DAYS = 30  # 30 kunlik faol bo‘lmaslik holati
INACTIVITY_THRESHOLD_2DAYS = 2  # 2 kunlik faol bo‘lmaslik holati
PERCENTAGE_TO_REMOVE_30DAYS = 45  # 30 kunlik faol bo‘lmaslik uchun olib tashlanadigan coin foizi
PERCENTAGE_TO_REMOVE_2DAYS = 85  # 2 kunlik faol bo‘lmaslik uchun olib tashlanadigan coin foizi

# Hozirgi narxni olish va yangilash
def update_coin_price():
    global current_price_index, price_last_updated
    now = datetime.now()
    if now - price_last_updated >= timedelta(hours=3):  # Har 3 soatda o‘zgaradi
        current_price_index = (current_price_index + 1) % len(COIN_PRICES)
        price_last_updated = now

def get_current_coin_price():
    update_coin_price()
    return COIN_PRICES[current_price_index]

# Balansni dollarda hisoblash
def calculate_balance_in_usd(coins):
    current_price = get_current_coin_price()
    return coins * current_price

# Faol bo‘lmagan foydalanuvchilarni tekshirish
def check_inactive_users():
    global total_hidden_coins
    now = datetime.now()
    for user_id, user_data in users.items():
        last_active = user_data.get('last_active', None)
        if last_active:
            days_inactive = (now - last_active).days

            if days_inactive >= INACTIVITY_THRESHOLD_30DAYS:
                # 30 kunlik faol bo‘lmaslik
                coins_to_remove = user_data['coins'] * PERCENTAGE_TO_REMOVE_30DAYS / 100
                user_data['coins'] -= coins_to_remove
                total_hidden_coins -= coins_to_remove

                bot.send_message(
                    user_id,
                    f"Siz botda 30 kun davomida faol bo‘lmadingiz. "
                    f"Balansingizdan {coins_to_remove:.2f} Hiden Coin olib tashlandi. "
                    f"Yangi balans: {user_data['coins']:.2f} Hiden Coin."
                )

            elif days_inactive >= INACTIVITY_THRESHOLD_2DAYS:
                # 2 kunlik faol bo‘lmaslik
                coins_to_remove = user_data['coins'] * PERCENTAGE_TO_REMOVE_2DAYS / 100
                user_data['coins'] -= coins_to_remove
                total_hidden_coins -= coins_to_remove

                bot.send_message(
                    user_id,
                    f"Siz botda 2 kun davomida faol bo‘lmadingiz. "
                    f"Balansingizdan {coins_to_remove:.2f} Hiden Coin olib tashlandi. "
                    f"Yangi balans: {user_data['coins']:.2f} Hiden Coin."
                )

# Har qanday xabarni foydalanuvchini faol deb belgilash uchun kuzatish
@bot.message_handler(func=lambda message: True)
def update_user_activity(message):
    user_id = message.from_user.id
    if user_id in users:
        users[user_id]['last_active'] = datetime.now()
    bot.reply_to(message, "Sizning faoliyatingiz qayd etildi.")

# Kunlik mukofotni olish
@bot.message_handler(commands=['daily'])
def daily_reward(message):
    global total_hidden_coins
    user_id = message.from_user.id
    if user_id not in users:
        bot.reply_to(message, "Iltimos, avval ro‘yxatdan o‘tib, kanalga obuna bo‘ling!")
        return

    user = users[user_id]
    if 'last_claim_time' in user and datetime.now() - user['last_claim_time'] < timedelta(hours=17):
        bot.reply_to(message, "Kunlik mukofotni olish vaqti hali yetib kelmadi!")
        return

    user['coins'] += HIDDEN_COIN_DAILY
    user['last_claim_time'] = datetime.now()
    total_hidden_coins += HIDDEN_COIN_DAILY

    balance_in_usd = calculate_balance_in_usd(user['coins'])

    bot.reply_to(
        message,
        f"Sizga {HIDDEN_COIN_DAILY} Hiden Coin berildi. "
        f"Yangi balans: {user['coins']} Hiden Coin (${balance_in_usd:.2f})."
    )

    # Jami ishlab chiqarilgan coinni tekshirish
    check_and_notify_airdrop()

# Jami coinni tekshirish va Airdropni faollashtirish
def check_and_notify_airdrop():
    global total_hidden_coins
    if total_hidden_coins >= MAX_HIDDEN_COINS:
        for user_id, user_data in users.items():
            bot.send_message(user_id, "Hiden Coin ishlab olish imkoniyati tugadi! Endi bepul Airdroplar boshlanadi!")

# Start komandasi: foydalanuvchini ro‘yxatdan o‘tkazish
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {
            'coins': 0,
            'tasks': [],
            'last_active': datetime.now(),
            'last_claim_time': None
        }
    bot.send_message(user_id, "Botga xush kelibsiz! Hamyonni ulash va vazifalarni bajarishni boshlashingiz mumkin.")

# Faol bo‘lmagan foydalanuvchilarni tekshirishni avtomatik chaqirish
def periodic_check():
    check_inactive_users()
    bot.send_message("ADMIN_ID", "Faol bo‘lmagan foydalanuvchilar tozalandi.")

# Periodik tekshirish uchun ishga tushirish
# schedule.every().day.at("00:00").do(periodic_check)
