# main.py — версия для python-telegram-bot 13.15
import os
import requests
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
)

# --------------------------------------------------------------------------
# ЗАГРУЗКА НАСТРОЕК .env
# --------------------------------------------------------------------------
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
AMO_API_URL = os.getenv("AMO_API_URL")
AMO_ACCESS_TOKEN = os.getenv("AMO_ACCESS_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL")
REF_LINK_WOMAN = os.getenv("REF_LINK_WOMAN")
REF_LINK_MAN = os.getenv("REF_LINK_MAN")
CONSULTANT_LINK = os.getenv("CONSULTANT_LINK")

# --------------------------------------------------------------------------
# ХРАНИЛИЩЕ ПОЛЬЗОВАТЕЛЕЙ (просто в памяти, для демо)
# --------------------------------------------------------------------------
user_state = {}  # {user_id: {role, points, gender, inviter_id}}

def clamp_points(points: int) -> int:
    return 20 if points > 20 else points

# --------------------------------------------------------------------------
# КНОПКИ
# --------------------------------------------------------------------------
def get_start_kb():
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("💚 Хочу здоровье", callback_data="role_health"),
            InlineKeyboardButton("💰 Хочу доход", callback_data="role_income"),
        ]]
    )

def get_health_kb1():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⚡ Энергия", callback_data="health_energy"),
                InlineKeyboardButton("🛡 Иммунитет", callback_data="health_immune"),
            ],
            [
                InlineKeyboardButton("😴 Сон", callback_data="health_sleep"),
                InlineKeyboardButton("🏃 Похудение", callback_data="health_fit"),
            ],
        ]
    )

def get_income_kb1():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💰 Доп. доход", callback_data="income_money"),
                InlineKeyboardButton("🌿 Развитие в wellness", callback_data="income_well"),
            ],
            [InlineKeyboardButton("✈️ Свобода и путешествия", callback_data="income_free")],
        ]
    )

def get_subscribe_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔔 Подписаться на канал", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ Я подписан(а)", callback_data="subscribed")],
        ]
    )

def get_gender_kb():
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("👩 Я женщина", callback_data="gender_woman"),
            InlineKeyboardButton("👨 Я мужчина", callback_data="gender_man"),
        ]]
    )

def get_finish_kb(ref_link: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton("💎 Забрать брильянты", url=ref_link)]])

# --------------------------------------------------------------------------
# Отправка данных в AMOCRM
# --------------------------------------------------------------------------
def send_to_amocrm(user_id: int):
    data = user_state[user_id]
    payload = {
        "name": str(user_id),
        "custom_fields_values": [
            {"field_name": "Telegram ID", "values": [{"value": user_id}]},
            {"field_name": "Категория", "values": [{"value": data.get('role')}]},
            {"field_name": "Пол", "values": [{"value": data.get('gender')}]},
            {"field_name": "Бриллианты", "values": [{"value": data.get('points')}]},
        ],
    }
    headers = {"Authorization": f"Bearer {AMO_ACCESS_TOKEN}", "Content-Type": "application/json"}
    try:
        requests.post(AMO_API_URL, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"AMOCRM send error: {e}")

# --------------------------------------------------------------------------
# START
# --------------------------------------------------------------------------
def start(update: Update, context: CallbackContext):
    """Обработка /start и приглашений"""
    inviter_id = None
    if context.args:
        try:
            inviter_id = int(context.args[0])
        except ValueError:
            inviter_id = None

    user_id = update.effective_user.id
    if user_id not in user_state:
        user_state[user_id] = {"role": None, "points": 0, "gender": None, "inviter_id": inviter_id}

    # если человек пришёл по реферальной ссылке
    if inviter_id and inviter_id in user_state:
        inviter = user_state[inviter_id]
        before = inviter["points"]
        inviter["points"] = clamp_points(inviter["points"] + 5)
        after = inviter["points"]
        context.bot.send_message(
            inviter_id,
            text=f"🎉 Твой друг перешёл по ссылке! +5 брильянтов 💎 (было {before} → {after})"
        )

    text = (
        "👋 Привет! Добро пожаловать в wellness‑проект.\n\n"
        "Выбери, что тебе ближе:"
    )
    update.message.reply_text(text, reply_markup=get_start_kb())

# --------------------------------------------------------------------------
# CALLBACKS
# --------------------------------------------------------------------------
def callback_router(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    query.answer()

    if user_id not in user_state:
        user_state[user_id] = {"role": None, "points": 0, "gender": None, "inviter_id": None}
    st = user_state[user_id]

    # роли
    if data == "role_health":
        st.update({"role": "Потребитель", "points": 0})
        query.message.reply_text("💚 Ответь на вопрос:", reply_markup=get_health_kb1())
        return
    if data == "role_income":
        st.update({"role": "Партнёр", "points": 0})
        query.message.reply_text("🔥 Зачем тебе удалённая работа?", reply_markup=get_income_kb1())
        return

    # ответы
    if data.startswith(("health_", "income_")):
        st["points"] = clamp_points(st["points"] + 5)
        query.message.reply_text(
            f"Отлично! У тебя {st['points']} брильянтов 💎.\n"
            "Теперь подпишись на канал, чтобы получить ещё + 5 💎",
            reply_markup=get_subscribe_kb(),
        )
        return

    # подписка
    if data == "subscribed":
        st["points"] = clamp_points(st["points"] + 10)
        query.message.reply_text(
            f"👏 Твой баланс: {st['points']} брильянтов 💎.\n"
            "Выбери свой пол, чтобы получить скидку 20 %:",
            reply_markup=get_gender_kb(),
        )
        return

    # выбор пола
    if data in ("gender_woman", "gender_man"):
        st["gender"] = "Женщина" if data == "gender_woman" else "Мужчина"
        st["points"] = 20
        send_to_amocrm(user_id)

        ref_link = REF_LINK_WOMAN if st["gender"] == "Женщина" else REF_LINK_MAN
        text = (
            f"💎 Поздравляю! Ты собрал {st['points']} брильянтов.\n"
            "Это скидка 20 % 🎁\n\n"
            "👉 Забери бонус ниже:"
        )
        query.message.reply_text(text, reply_markup=get_finish_kb(ref_link))

        bot_username = context.bot.username
        extra_menu = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("👥 Пригласить друга", callback_data="invite")],
                [InlineKeyboardButton("💎 Мой баланс", callback_data="balance")],
                [InlineKeyboardButton("📞 Связаться с консультантом", url=CONSULTANT_LINK)],
            ]
        )
        query.message.reply_text(
            "🎁 Хочешь поделиться игрой и помочь друзьям тоже получить скидку? (по желанию)",
            reply_markup=extra_menu,
        )
        return

    # пригласить друга
    if data == "invite":
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start={user_id}"
        text = (
            "👥 Поделись этой ссылкой с другом.\n"
            "Когда он пройдёт игру, ты получишь + 5 брильянтов (макс 20).\n\n"
            f"🔗 Твоя ссылка: {link}"
        )
        query.message.reply_text(text)
        return

    # баланс
    if data == "balance":
        query.message.reply_text(f"Твой текущий баланс: {st['points']} брильянтов 💎.")
        return

# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(callback_router))

    print("✅ Бот запущен. Нажмите Ctrl+C для остановки.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()