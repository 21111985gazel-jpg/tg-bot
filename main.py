# -*- coding: utf-8 -*-
"""
Wellness Quest Bot 💎
Игровой телеграм‑бот с сертификатом‑скидкой, рейтингом и соц‑механиками.
"""

import asyncio
import os
import io
import random
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import aiojobs

# === НАСТРОЙКИ ===
load_dotenv()

# Функция для чтения переменных из .env с удалением кавычек
def get_env(key, default=None):
    value = os.getenv(key, default)
    if value and isinstance(value, str):
        value = value.strip('"').strip("'")
    return value

BOT_TOKEN = get_env("BOT_TOKEN")
CHANNEL_ID = get_env("CHANNEL_ID")
AMO_DOMAIN = get_env("AMO_DOMAIN")
AMO_TOKEN = get_env("AMO_TOKEN")

if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в .env файле!")
    exit(1)

# Преобразуем CHANNEL_ID в int, если он указан
if CHANNEL_ID:
    try:
        CHANNEL_ID = int(CHANNEL_ID)
    except ValueError:
        print(f"⚠️ ВНИМАНИЕ: CHANNEL_ID '{CHANNEL_ID}' не является числом!")
        CHANNEL_ID = None

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# === ВРЕМЕННОЕ «ХРАНИЛИЩЕ» ===
users = {}  # user_id -> {name, role, points}
jobs_manager = None

# === ХЕЛПЕРЫ ===
def get_user(id, name='User'):
    if id not in users:
        users[id] = {"name": name, "role": None, "points": 0}
    return users[id]

def add_points(id, plus):
    u = get_user(id)
    u["points"] = min(u["points"] + plus, 20)
    return u["points"]

def progress_bar(points):
    filled = points // 5
    return f"Прогресс: {'💎' * filled}{'▫️' * (4 - filled)}\nСкидка: *{points}%*"

async def send_to_amocrm(name, username, role, points):
    if not AMO_DOMAIN or not AMO_TOKEN:
        return
    try:
        url = f"https://{AMO_DOMAIN}/api/v4/leads"
        headers = {"Authorization": f"Bearer {AMO_TOKEN}"}
        data = [{
            "name": f"{role.upper()} — {name}",
            "custom_fields_values": [
                {"field_name": "Telegram", "values": [{"value": username}]},
                {"field_name": "Points", "values": [{"value": points}]}
            ]
        }]
        requests.post(url, json=data, headers=headers, timeout=5)
    except Exception as e:
        print("AmoCRM error:", e)

# === СЕРТИФИКАТ КАК PNG ===
def generate_certificate(name, points, role):
    # Ленивая загрузка PIL только когда нужно генерировать сертификат
    from PIL import Image, ImageDraw, ImageFont
    
    width, height = 800, 450
    img = Image.new("RGB", (width, height), color=(230, 248, 245))
    draw = ImageDraw.Draw(img)
    
    # Используем дефолтный шрифт, если системный не найден
    try:
        title_font = ImageFont.truetype("arial.ttf", 34)
        body_font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 34)
            body_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
    
    # Фон уже установлен при создании изображения
    draw.text((50, 80), "WELLNESS QUEST CERTIFICATE", font=title_font, fill=(0, 100, 90))
    draw.text((60, 150), f"Имя: {name}", font=body_font, fill=(10, 30, 30))
    draw.text((60, 190), f"Роль: {'Партнёр' if role == 'partner' else 'Потребитель'}", font=body_font, fill=(10, 30, 30))
    draw.text((60, 230), f"Бриллиантов 💎: {points}", font=body_font, fill=(0, 150, 130))
    draw.text((60, 270), f"Бонус / скидка: {points}% 🇨🇦", font=body_font, fill=(0, 120, 100))
    draw.text((60, 340), "Поздравляем и желаем здоровья и энергии 🌿", font=body_font, fill=(0, 120, 100))
    
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf

# === КОМАНДЫ ===

# /start
@dp.message(Command("start"))
async def start_cmd(msg: Message):
    chat_id = msg.chat.id
    name = msg.from_user.first_name or "Друг"
    
    users[chat_id] = {"name": name, "role": None, "points": 0}
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💚 Прокачать здоровье", callback_data="consumer")],
        [InlineKeyboardButton(text="💰 Хочу доход онлайн", callback_data="partner")]
    ])
    
    await msg.answer(
        f"Привет, {name}! 👋\nДобро пожаловать в *Wellness Quest* 💎\n\n"
        "Здесь можно:\n💚 улучшить самочувствие и получить скидку\n"
        "💰 узнать, как создать доход онлайн\n\nВыбирай направление 👇",
        reply_markup=kb
    )

# === ВЫБОР РОЛИ ===
@dp.callback_query(F.data.in_({"consumer", "partner"}))
async def choose_role(call: CallbackQuery):
    chat_id = call.message.chat.id
    user = get_user(chat_id, call.from_user.first_name)
    
    user["role"] = call.data
    add_points(chat_id, 5)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на wellness‑канал", url="https://t.me/your_channel")],
        [InlineKeyboardButton(text="▶️ Начать игру", callback_data="quiz1")]
    ])
    
    await call.message.edit_text(
        f"Ты получил 5 бриллиантов 💎 за старт!\n\n{progress_bar(user['points'])}",
        reply_markup=kb
    )
    await call.answer()

# === ВИКТОРИНА ===
QUIZZES = [
    "💧 Сколько воды ты пьёшь в день?",
    "😴 Высыпаешься ли ночью?",
    "🥗 Есть ли овощи и фрукты в рационе?",
    "🚶 Двигаешься ли хотя бы 30 минут в день?"
]

@dp.callback_query(F.data.startswith("quiz"))
async def quiz_handler(call: CallbackQuery):
    chat_id = call.message.chat.id
    user = get_user(chat_id)
    
    step = int(call.data.replace("quiz", ""))
    if step > len(QUIZZES):
        await finish_quest(chat_id)
        await call.answer()
        return
    
    q = QUIZZES[step - 1]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"quiz{step + 1}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"quiz{step + 1}")
        ]
    ])
    
    await call.message.edit_text(
        f"{q}\n\n{progress_bar(user['points'])}",
        reply_markup=kb
    )
    await call.answer()

# === ФИНАЛ КВЕСТА ===
async def finish_quest(chat_id):
    u = get_user(chat_id)
    add_points(chat_id, 15)
    
    # Анимация роста
    for p in range(5, 21, 5):
        await bot.send_message(chat_id, f"✨ Считаем бриллианты...\n{progress_bar(p)}")
        await asyncio.sleep(0.4)
    
    certificate = generate_certificate(u["name"], u["points"], u["role"])
    link = "https://your_ref_link.coralmembership.com" if u["role"] == "consumer" else "https://t.me/your_partner_chat"
    caption = (
        f"🎉 Поздравляем, {u['name']}!\nТы собрал 20 бриллиантов 💎 и получил 20 % скидки 🇨🇦"
        if u["role"] == "consumer"
        else f"🚀 Поздравляем, {u['name']}!\nТы собрал 20 бриллиантов 💎 и стал Ambassador PRO 💼"
    )
    
    await send_to_amocrm(u["name"], str(chat_id), u["role"], u["points"])
    
    photo = FSInputFile(certificate, filename="certificate.png")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Активировать бонус", url=link)],
        [InlineKeyboardButton(text="💬 Поделиться сертификатом", callback_data=f"share_{chat_id}")],
        [InlineKeyboardButton(text="📊 Рейтинг", callback_data="rating")]
    ])
    
    await bot.send_photo(chat_id, photo, caption=caption, reply_markup=kb)

# === СОЦИАЛЬНЫЕ МЕХАНИКИ ===
@dp.callback_query(F.data.startswith("share_"))
async def cb_share(call: CallbackQuery):
    chat_id = call.message.chat.id
    u = get_user(chat_id)
    bot_username = (await bot.get_me()).username
    share_text = f"Я прошёл Wellness Quest и получил {u['points']} бриллиантов 💎!\nПопробуй и ты 👉 t.me/{bot_username}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Поделиться", switch_inline_query=share_text)]
    ])
    
    await call.message.answer("Поделись результатом 👇", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data == "rating")
async def cb_rating(call: CallbackQuery):
    chat_id = call.message.chat.id
    
    top = sorted(users.values(), key=lambda x: x["points"], reverse=True)[:5]
    msg_txt = "🏆 *ТОП‑5 бриллиантовых героев:*\n\n"
    for i, u in enumerate(top, start=1):
        msg_txt += f"{i}. {u['name']} — {u['points']} 💎\n"
    
    await call.message.answer(msg_txt)
    await call.answer()

# === ЕЖЕДНЕВНЫЙ WELLNESS‑БОСТ ===
MESSAGES = [
    "💧 Пора выпить воду и зарядиться энергией!",
    "🌿 Сделай 5 глубоких вдохов!",
    "☀️ Проверь осанку и улыбнись 😄"
]

async def daily_broadcast(bot: Bot):
    while True:
        text = random.choice(MESSAGES)
        for chat_id in list(users.keys()):
            try:
                await bot.send_message(chat_id, text)
            except:
                continue
        await asyncio.sleep(24 * 60 * 60)  # раз в сутки

# === ЗАПУСК ===
# Ежедневная рассылка отключена (раскомментируйте, если нужна)
# @dp.startup()
# async def on_startup():
#     global jobs_manager
#     jobs_manager = await aiojobs.create_scheduler()
#     await jobs_manager.spawn(daily_broadcast(bot))
#     print("Daily broadcast task started")

async def main():
    print("🤖 Wellness Quest бот запущен...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())

